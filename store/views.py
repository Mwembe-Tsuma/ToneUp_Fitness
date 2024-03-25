from django.shortcuts import render, redirect
from django.http import JsonResponse
import json
import datetime
from .models import * 
from .utils import cookieCart, cartData, guestOrder
from django.contrib.auth import authenticate, login, logout

# validation
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.core.exceptions import ValidationError


# register
def register(request):
    if request.user.is_authenticated:
        return redirect("/")
    else:
        if request.method == "POST":
            if 'full_name' in request.POST:
                username = request.POST['username']
                full_name = request.POST['full_name']
                password1 = request.POST['password1']
                password2 = request.POST['password2']
                email = request.POST['email']

                if any(char.isdigit() for char in username):
                    alert = True
                    return render(request, "store/register.html", {'alert': alert, 'message': 'Username cannot contain numbers'})

                if any(char.isdigit() for char in full_name):
                    alert = True
                    return render(request, "store/register.html", {'alert': alert, 'message': 'Full name cannot contain numbers'})

                try:
                    validate_password(password1)
                except ValidationError as e:
                    alert = True
                    return render(request, "store/register.html", {'alert': alert, 'message': e.messages[0]})

                if password1 != password2:
                    alert = True
                    return render(request, "store/register.html", {'alert': alert, 'message': 'Passwords do not match'})

                try:
                    validate_email(email)
                except ValidationError:
                    alert = True
                    return render(request, "store/register.html", {'alert': alert, 'message': 'Invalid email address'})

                if User.objects.filter(username=username).exists():
                    alert = True
                    return render(request, "store/register.html", {'alert': alert, 'message': 'Username already in use'})

                if User.objects.filter(email=email).exists():
                    alert = True
                    return render(request, "store/register.html", {'alert': alert, 'message': 'Email address already in use'})

                user = User.objects.create_user(username=username, password=password1, email=email)
                customer = Customer.objects.create(user=user, name=full_name, email=email)

                user = authenticate(request, username=username, password=password1)
                login(request, user)

                return redirect("store")

            else:
                alert = True
                return render(request, "store/register.html", {'alert': alert, 'message': 'Invalid registration details'})
    
    return render(request, "store/register.html")

# login
def Login(request):
    if request.user.is_authenticated:
        return redirect("/")
    else:
        if request.method == "POST":
            username = request.POST['username']
            password = request.POST['password']
            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                print("User authenticated successfully.")
                return redirect("/")
            else:
                alert = True
                error_message = "Incorrect username or password. Please try again."
                return render(request, "store/login.html", {"alert": alert, "error_message": error_message})
    return render(request, "store/login.html")

# logout
def Logout(request):
    logout(request)
    alert = True
    return redirect("store")

# when use is logged in
def loggedin_contact(request):
    data = cartData(request)
    items = data['items']
    order = data['order']
    cartItems = data['cartItems']
    if request.method=="POST":       
        name = request.user
        email = request.user.email
        phone = request.user.customer.phone_number
        desc = request.POST['desc']
        contact = UserContact(name=name, email=email, desc=desc)
        contact.save()
        alert = True
        return render(request, 'loggedin_contact.html', {'alert':alert})
    return render(request, "store/loggedin_contact.html", {'cartItems':cartItems})

# change password
def change_password(request):
    if not request.user.is_authenticated:
        return redirect('/login')
    data = cartData(request)
    items = data['items']
    order = data['order']
    cartItems = data['cartItems']
    if request.method == "POST":
        current_password = request.POST['current_password']
        new_password = request.POST['new_password']
        try:
            u = User.objects.get(id=request.user.id)
            if u.check_password(current_password):
                u.set_password(new_password)
                u.save()
                alert = True
                return render(request, "change_password.html", {'alert':alert})
            else:
                currpasswrong = True
                return render(request, "change_password.html", {'currpasswrong':currpasswrong})
        except:
            pass
    return render(request, "store/change_password.html", {'cartItems':cartItems})

def store(request):
	data = cartData(request)

	cartItems = data['cartItems']
	order = data['order']
	items = data['items']

	products = Product.objects.all()
	context = {'products':products, 'cartItems':cartItems}
	return render(request, 'store/store.html', context)


def cart(request):
	data = cartData(request)

	cartItems = data['cartItems']
	order = data['order']
	items = data['items']

	context = {'items':items, 'order':order, 'cartItems':cartItems}
	return render(request, 'store/cart.html', context)

def checkout(request):
	data = cartData(request)
	
	cartItems = data['cartItems']
	order = data['order']
	items = data['items']

	context = {'items':items, 'order':order, 'cartItems':cartItems}
	return render(request, 'store/checkout.html', context)

def updateItem(request):
	data = json.loads(request.body)
	productId = data['productId']
	action = data['action']
	print('Action:', action)
	print('Product:', productId)

	customer = request.user.customer
	product = Product.objects.get(id=productId)
	order, created = Order.objects.get_or_create(customer=customer, complete=False)

	orderItem, created = OrderItem.objects.get_or_create(order=order, product=product)

	if action == 'add':
		orderItem.quantity = (orderItem.quantity + 1)
	elif action == 'remove':
		orderItem.quantity = (orderItem.quantity - 1)

	orderItem.save()

	if orderItem.quantity <= 0:
		orderItem.delete()

	return JsonResponse('Item was added', safe=False)

def processOrder(request):
	transaction_id = datetime.datetime.now().timestamp()
	data = json.loads(request.body)

	if request.user.is_authenticated:
		customer = request.user.customer
		order, created = Order.objects.get_or_create(customer=customer, complete=False)
	else:
		customer, order = guestOrder(request, data)

	total = float(data['form']['total'])
	order.transaction_id = transaction_id

	if total == order.get_cart_total:
		order.complete = True
	order.save()

	if order.shipping == True:
		ShippingAddress.objects.create(
		customer=customer,
		order=order,
		address=data['shipping']['address'],
		city=data['shipping']['city'],
		state=data['shipping']['state'],
		zipcode=data['shipping']['zipcode'],
		)

	return JsonResponse('Payment submitted..', safe=False)