from django.urls import path

from . import views

urlpatterns = [
	#Leave as empty string for base url
	path('', views.store, name="store"),
	path('cart/', views.cart, name="cart"),
	path('checkout/', views.checkout, name="checkout"),

	path('update_item/', views.updateItem, name="update_item"),
	path('process_order/', views.processOrder, name="process_order"),
    path("register/", views.register, name="register"),
    path("login/", views.Login, name="login"),
    path("logout/", views.Logout, name="logout"),
    path("change_password/", views.change_password, name="change_password"),
    path("loggedin_contact/", views.loggedin_contact, name="loggedin_contact"),
    path('about/', views.about, name='about'),
	path('contact/', views.contact, name='contact'),
]