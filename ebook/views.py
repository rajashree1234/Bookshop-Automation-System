from django.conf import settings
from django.http import HttpResponse
from django.contrib import messages
from django.template.defaultfilters import slugify
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render, get_object_or_404, redirect, reverse
from django.utils import timezone
from datetime import datetime
from django.views.generic import ListView, DetailView, View
from taggit.models import Tag
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.core.mail import EmailMessage, send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.db.models import Q
import razorpay
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt, csrf_protect

from .models import (Book, OrderItem, Order, Payment, Coupon, Refund, 
                    Address, UserProfile, Seller, SellerSale, CATEGORY_CHOICES, Wishlist, CarauselImage, SidePanelImages)

from .forms import (CheckoutForm, CouponForm, RefundForm, PaymentForm, AddBookForm, 
                    AddSellerForm, BookUpdateForm, UserUpdateForm,
                    ActivateSellerForm, ReferalForm)

def create_ref_code():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))


def is_valid_form(values):
    valid = True
    for field in values:
        if field == '':
            valid = False
    return valid

def home(request):
    context={}
    carausel_images = CarauselImage.objects.all()
    language = request.GET.get('language')
    try:
        right_panel_img1 = SidePanelImages.objects.get(position='first_image')
        context['right_panel_img1'] = right_panel_img1
        right_panel_img2 = SidePanelImages.objects.get(position='second_image')
        context['right_panel_img2'] = right_panel_img2
        right_panel_vid = SidePanelImages.objects.get(position='yt_video_link')
        context['right_panel_vid'] = right_panel_vid
        print('sucess')
    except:
        pass
        print('failed')
    search = request.GET.get('q')
    if language:
        all_books = Book.objects.filter(language=language).order_by('title')
    elif request.GET.get('q'):
        # books = get_book_queryset(search)
        # context['books'] = books
        # return render(request, 'bookstore/book_list.html', context)
        return redirect('/search-result/' + search)
        # return reverse("search-result", kwargs={
        #     'search': search
        # })
    else:
        all_books = Book.objects.order_by('title')
    all_books_p = Paginator(all_books, 28)
    page = request.GET.get('page')

    categories = []
    for c in CATEGORY_CHOICES:
        categories.append((c[0], c[1]))
    
    all_books = all_books_p.get_page(page)
    context['all_books'] = all_books
    context['all_authors'] = Book.objects.values_list('author', flat=True).distinct()
    context['all_categories'] = categories
    context['carausel_images'] = carausel_images
    

    return render(request, 'bookstore/home.html', context)


def AuthorBookList(request, author):
    if request.GET.get('q'):
        search = request.GET.get('q')
        return redirect('/search-result/' + search)
    author = author.replace('%20', ' ')
    context = {}
    all_books = Book.objects.filter(author=author)
    
    all_books_p = Paginator(all_books, 10)
    page = request.GET.get('page')
    all_books = all_books_p.get_page(page)

    context['books'] = all_books
    return render(request, 'bookstore/book_list.html', context)


def CategoryBookList(request, category):
    if request.GET.get('q'):
        search = request.GET.get('q')
        return redirect('/search-result/' + search)
    category = category.replace('%20', ' ')
    context = {}
    all_books = Book.objects.filter(category=category)
    

    all_books_p = Paginator(all_books, 10)
    page = request.GET.get('page')
    all_books = all_books_p.get_page(page)

    context['books'] = all_books

    return render(request, 'bookstore/book_list.html', context)

class ItemDetailView(DetailView):
    model = Book
    template_name = "bookstore/product_detail.html"



class SellerBooks(ListView):
    paginate_by = 20
    template_name = 'bookstore/seller_books.html'
    context_object_name = 'all_books'
    # ordering = ['-date_posted']
    def get_queryset(self):
        curr_seller = Seller.objects.get(user=self.request.user)
        all_books = Book.objects.filter(seller=curr_seller)
        return all_books


class BookList(ListView):
    model = Book
    paginate_by = 5
    template_name = "bookstore/book_list.html"
    context_object_name = 'books'


@login_required
def profile(request):
    if request.GET.get('q'):
        search = request.GET.get('q')
        return redirect('/search-result/' + search)
    if request.method == 'POST':
        seller_form = AddSellerForm(request.POST)
        user_form = UserUpdateForm(request.POST)
        if user_form.is_valid():
            update_user = request.user
            update_user.first_name = user_form.cleaned_data.get('first_name')
            update_user.last_name = user_form.cleaned_data.get('last_name')
            update_user.username = user_form.cleaned_data.get('username')
            update_user.email = user_form.cleaned_data.get('email')
            update_user.save()
            if not request.user.is_seller:
                messages.info(request, "User details updated")
                return redirect('/profile')
        else:
            messages.warning(request, "Invalid entry!")
            return redirect('/profile')
        if seller_form.is_valid():
            if request.user.is_seller():
                update_seller = Seller.objects.get(user=request.user)
                update_seller.phone_number = seller_form.cleaned_data.get('phone_number')
                update_seller.save()
                messages.info(request, "Profile updated!")
                return redirect("/profile")
        
        else:
            messages.warning(request, "Invalid seller details")
            return redirect("/profile")


    seller_form = AddSellerForm()
    user_form = UserUpdateForm()
    if request.user.is_seller():
        seller_details = Seller.objects.get(user=request.user)
        seller_orders = SellerSale.objects.filter(seller=seller_details)
        seller_books = Book.objects.filter(seller=seller_details)
        context = {
            'seller_orders': seller_orders,
            'seller_details': seller_details,
            'seller_form': seller_form,
            'user_form': user_form,
            'seller_books': seller_books
        }
    else:
        context = {
            'user_form': user_form
        }
    
    return render(request, 'bookstore/profile.html', context)


@login_required
def add_seller(request):
    if request.method == 'POST':
        form = AddSellerForm(request.POST)
        user_form = UserUpdateForm(request.POST)
        if user_form.is_valid():
            update_user = request.user
            update_user.first_name = user_form.cleaned_data.get('first_name')
            update_user.last_name = user_form.cleaned_data.get('last_name')
            update_user.username = user_form.cleaned_data.get('username')
            update_user.email = user_form.cleaned_data.get('email')
            update_user.save()
        else:
            messages.warning(request, "Please check the user details again")
            return redirect("/add-seller")
        if form.is_valid():
            newseller = Seller()
            newseller.ref_code = create_ref_code()
            newseller.user = request.user
            newseller.phone_number = form.cleaned_data.get('phone_number')
            newseller.save()
            mail_subject = 'Sellers account activation'
            mail_body = f'Hello {newseller.user.first_name} Your sellers account activation code is : {newseller.ref_code}'
            send_mail(
                mail_subject,
                mail_body,
                SENDER_EMAIL,
                [newseller.user.email]
            )
            messages.info(request, f'Account created!! Please activate your account through the code sent to {newseller.user.email}')
            return redirect("/activate-sellers-account")
        else:
            print(form.errors)
            messages.warning(request, "Please check the entries again")
            return redirect("/add-seller")

    else:
        user_form = UserUpdateForm()
        form = AddSellerForm()
        user_details = request.user
        context = {
            'form': form,
            'user_form': user_form,
            'user_details': user_details
        }
        return render(request, 'bookstore/add_seller.html', context)


@login_required
def add_book(request):
    # Show most common tags
    try:
        curr_seller = Seller.objects.get(user=request.user)
        common_tags = Book.tags.most_common()[:5]
        if request.method == 'POST':
            form = AddBookForm(request.POST, request.FILES)
            if form.is_valid():
                newbook = form.save(commit=False)
                newbook.slug = slugify(newbook.title)
                newbook.seller = curr_seller
                newbook.save()
                form.save_m2m()
                messages.info(request, "The book was added")
                return redirect("/")
            else:
                print(form.errors)
                messages.warning(request, "The book was not added")
                return redirect("/add-book")

        else:
            form = AddBookForm()
            context = {
                'form': form,
                'common_tags': common_tags,
            }
            return render(request, 'bookstore/add_book.html', context)
    # except OperationalError:
    #     messages.warning(request, "Invalid Data Entry")
    #     return redirect('/add-seller')
    except:
        messages.warning(request, "Either the data was invalid or you don't have a sellers account!")
        return redirect('/add-book')

@login_required
def update_book(request, slug):
    book = get_object_or_404(Book, slug=slug)
    if request.method == 'POST':
        u_form = BookUpdateForm(request.POST, request.FILES, instance=book)

        if u_form.is_valid():
            u_form.save()
            messages.info(request, "The book was updated")
            return redirect("update-book", slug=slug)
        
        else:
            messages.warning(request, "Invalid entry")

    else:
        u_form = BookUpdateForm(instance=book)

    context = {
        'u_form': u_form,
    }
    return render(request, 'bookstore/update_book.html', context)

@login_required
def add_to_wishlist(request, slug):
    item = get_object_or_404(Book, slug=slug)
    W, created = Wishlist.objects.get_or_create(user=request.user)
    if W.items.filter(slug=slug).exists():
        messages.info(request, "Item already in your wishlist")
        return redirect("product-detail", slug=slug)
    else:
        W.items.add(item)
        W.save()
        messages.info(request, "Item was added to your wishlist!")
        return redirect("product-detail", slug=slug)

@login_required
def remove_from_wishlist(request, slug):
    item = get_object_or_404(Book, slug=slug)
    wlist = Wishlist.objects.get(user=request.user)
    wlist.items.remove(item)
    wlist.save()
    messages.info(request, "This item was removed from your wishlist!")
    return redirect("product-detail", slug=slug)

@login_required
def my_wishlist(request):
    context={}
    wishlist = get_object_or_404(Wishlist, user=request.user)
    context['books'] = wishlist.items.all()
    context['is_wish_page'] = True
    context['message'] = 'Your Wishlist'
    return render(request, 'bookstore/book_list.html', context)


@login_required
def add_to_cart(request, slug):
    item = get_object_or_404(Book, slug=slug)
    order_item, created = OrderItem.objects.get_or_create(
        item=item,
        user=request.user,
        ordered=False
    )
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        # check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item.quantity += 1
            order_item.save()
            messages.info(request, "This item quantity was updated in your cart.")
        else:
            messages.info(request, "This item was added to your cart.")
            order.items.add(order_item)
            return redirect("product-detail", slug=slug)
    else:
        order = Order.objects.create(
            user=request.user)
        order.items.add(order_item)
        messages.info(request, "This item was added to your cart.")
    return redirect("product-detail", slug=slug)


@login_required
def remove_from_cart(request, slug):
    item = get_object_or_404(Book, slug=slug)
    order_qs = Order.objects.filter(
        user=request.user,
        ordered=False
    )
    if order_qs.exists():
        order = order_qs[0]
        # check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(
                item=item,
                user=request.user,
                ordered=False
            )[0]
            order.items.remove(order_item)
            order_item.delete()
            messages.info(request, "Item Removed!")
            return redirect("order-summary")
        else:
            messages.info(request, "This item was not in your cart.")
            return redirect("product-detail", slug=slug)

    else:
        messages.info(request, "You do not have an active order.")
        return redirect("product-detail", slug=slug)
    

@login_required
def remove_single_item_from_cart(request, slug):
    item = get_object_or_404(Book, slug=slug)
    order_qs = Order.objects.filter(
        user=request.user,
        ordered=False
    )
    if order_qs.exists():
        order = order_qs[0]
        # check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(
                item=item,
                user=request.user,
                ordered=False
            )[0]
            if order_item.quantity > 1:
                order_item.quantity -= 1
                order_item.save()
            else:
                order.items.remove(order_item)
            messages.info(request, "Item quantity was updated.")
            return redirect("order-summary")
        else:
            messages.info(request, "This item was not in your cart")
            return redirect("product-detail", slug=slug)
    else:
        messages.info(request, "You do not have an active order! Try adding items to your cart.")
        return redirect("product-detail", slug=slug)

class AddCouponView(View):
    def post(self, *args, **kwargs):
        form = CouponForm(self.request.POST or None)
        if form.is_valid():
            try:
                code = form.cleaned_data.get('code')
                order = Order.objects.get(
                    user=self.request.user, ordered=False)
                order.coupon = get_coupon(self.request, code)
                order.save()
                messages.success(self.request, "Successfully added coupon")
                return redirect("checkout")
            except ObjectDoesNotExist:
                messages.info(self.request, "You do not have an active order")
                return redirect("checkout")
            except ValueError:
                messages.info(self.request, "Invalid coupan!")
                return redirect("checkout!")

class OrderSummaryView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            context = {
                'object': order
            }
            return render(self.request, 'bookstore/order_summary.html', context)
        except ObjectDoesNotExist:
            messages.warning(self.request, "You do not have an active order")
            return redirect("/")


@login_required
def my_orders(request):
    if request.GET.get('q'):
        search = request.GET.get('q')
        return redirect('/search-result/' + search)
    orders = Order.objects.filter(user=request.user).order_by("-ordered_date")
    context = {
        'orders': orders
    }
    return render(request, 'bookstore/my_orders.html', context)


class CheckoutView(View):
    def get(self, *args, **kwargs):
        try:
            if self.request.GET.get('q'):
                search = self.request.GET.get('q')
                return redirect('/search-result/' + search)
            order = Order.objects.get(user=self.request.user, ordered=False)
            form = CheckoutForm()
            context = {
                'form': form,
                'couponform': CouponForm(),
                'referalform': ReferalForm(),
                'order': order,
                'DISPLAY_COUPON_FORM': True
            }

            shipping_address_qs = Address.objects.filter(
                user=self.request.user,
                address_type='S',
                default=True
            )
            if shipping_address_qs.exists():
                context.update(
                    {'default_shipping_address': shipping_address_qs[0]})

            billing_address_qs = Address.objects.filter(
                user=self.request.user,
                address_type='B',
                default=True
            )
            if billing_address_qs.exists():
                context.update(
                    {'default_billing_address': billing_address_qs[0]})
            return render(self.request, "bookstore/checkout.html", context)
        except ObjectDoesNotExist:
            messages.info(self.request, "You do not have an active order")
            return redirect("checkout")

    def post(self, *args, **kwargs):
        form = CheckoutForm(self.request.POST)
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            print(form.errors)
            if form.is_valid():

                order.email = form.cleaned_data.get('email')
                order.firstname = form.cleaned_data.get('firstname')
                order.lastname = form.cleaned_data.get('lastname')
                order.phone_number = form.cleaned_data.get('phone_number')
                use_default_shipping = form.cleaned_data.get(
                    'use_default_shipping')
                if use_default_shipping:
                    print("Using the defualt shipping address")
                    address_qs = Address.objects.filter(
                        user=self.request.user,
                        address_type='S',
                        default=True
                    )
                    if address_qs.exists():
                        shipping_address = address_qs[0]
                        order.shipping_address = shipping_address
                        order.save()
                    else:
                        messages.info(
                            self.request, "No default shipping address available")
                        return redirect('checkout')
                else:
                    print("User is entering a new shipping address")
                    shipping_address1 = form.cleaned_data.get(
                        'shipping_address')
                    shipping_address2 = form.cleaned_data.get(
                        'shipping_address2')
                    shipping_country = form.cleaned_data.get(
                        'shipping_country')
                    scity = form.cleaned_data.get(
                        'scity')
                    sdistrict = form.cleaned_data.get(
                        'sdistrict')
                    sstate = form.cleaned_data.get(
                        'sstate')
                    shipping_zip = form.cleaned_data.get('shipping_zip')

                    if is_valid_form([shipping_address1, shipping_country, shipping_zip]):
                        shipping_address = Address(
                            user=self.request.user,
                            street_address=shipping_address1,
                            apartment_address=shipping_address2,
                            city = scity,
                            district = sdistrict,
                            state = sstate,
                            country=shipping_country,
                            zip=shipping_zip,
                            address_type='S'
                        )
                        shipping_address.save()

                        order.shipping_address = shipping_address
                        order.save()

                        set_default_shipping = form.cleaned_data.get(
                            'set_default_shipping')
                        if set_default_shipping:
                            shipping_address.default = True
                            shipping_address.save()

                    else:
                        messages.info(
                            self.request, "Please fill in the required shipping address fields")

                use_default_billing = form.cleaned_data.get(
                    'use_default_billing')
                same_billing_address = form.cleaned_data.get(
                    'same_billing_address')

                if same_billing_address:
                    billing_address = shipping_address
                    billing_address.pk = None
                    billing_address.save()
                    billing_address.address_type = 'B'
                    billing_address.save()
                    order.billing_address = billing_address
                    order.save()

                elif use_default_billing:
                    print("Using the defualt billing address")
                    address_qs = Address.objects.filter(
                        user=self.request.user,
                        address_type='B',
                        default=True
                    )
                    if address_qs.exists():
                        billing_address = address_qs[0]
                        order.billing_address = billing_address
                        order.save()
                    else:
                        messages.info(
                            self.request, "No default billing address available")
                        return redirect('checkout')
                else:
                    print("User is entering a new billing address")
                    billing_address1 = form.cleaned_data.get(
                        'billing_address')
                    billing_address2 = form.cleaned_data.get(
                        'billing_address2')
                    billing_country = form.cleaned_data.get(
                        'billing_country')
                    bcity = form.cleaned_data.get(
                        'bcity')
                    bdistrict = form.cleaned_data.get(
                        'bdistrict')
                    bstate = form.cleaned_data.get(
                        'bstate')
                    billing_zip = form.cleaned_data.get('billing_zip')

                    if is_valid_form([billing_address1, billing_country, billing_zip]):
                        billing_address = Address(
                            user=self.request.user,
                            street_address=billing_address1,
                            apartment_address=billing_address2,
                            city = bcity,
                            district = bdistrict,
                            state = bstate,
                            country=billing_country,
                            zip=billing_zip,
                            address_type='B'
                        )
                        billing_address.save()

                        order.billing_address = billing_address
                        order.save()

                        set_default_billing = form.cleaned_data.get(
                            'set_default_billing')
                        if set_default_billing:
                            billing_address.default = True
                            billing_address.save()

                    else:
                        messages.info(
                            self.request, "Please fill in the required billing address fields")

                payment_option = 'R'

                if payment_option == 'S':
                    return redirect('payment', payment_option='stripe')
                elif payment_option == 'P':
                    return redirect('payment', payment_option='paypal')
                elif payment_option == 'R':
                    return redirect('/payment')
                else:
                    messages.warning(
                        self.request, "Invalid payment option selected")
                    return redirect('checkout')
            else:
                messages.warning(self.request, "Invalid Form!")
                return redirect("checkout")
            messages.warning(self.request, "some error occured")
            return redirect("checkout")
        except:
            messages.warning(self.request, "You do not have an active order")
            return redirect("order-summary")


def payment(request):
    if request.GET.get('q'):
        search = request.GET.get('q')
        return redirect('/search-result/' + search)
    order = Order.objects.get(user=request.user, ordered=False)
    amount = int(order.get_total()) * 100
    order_currency = 'INR'
    
    # if not order.is_payment_pending():
    payment = client.order.create({'amount':amount, 
                                    'currency':'INR', 
                                    'payment_capture': '1'})
    order.rp_order_id = payment['id']
    order.save()
    order_items = order.items.all()
    order_items.update(rp_order_id=payment['id'])
    for item in order_items:
        item.save()
    print(payment)
    context = {
        'ramount': int(order.get_total()),
        'amount': amount,
        'order': order,
        'key_id': RAZORPAY_KEY_ID
    }
    return render(request, "bookstore/payment.html", context)


def send_mail_to_seller(sellersale):
    context = {
        "seller_order_details": sellersale
    }
    html_content = render_to_string("confirmations/seller_order_details_mail.html", context)
    text_content = strip_tags(html_content)
    email = EmailMultiAlternatives(
        "Book Purchased",
        text_content,
        SENDER_EMAIL,
        [sellersale.seller.user.email]
    )
    email.attach_alternative(html_content, "text/html")
    email.send()

def send_mail_to_buyer(order):
    context = {
        'order': order
    }
    html_content = render_to_string("confirmations/buyer_order_details_mail.html", context)
    text_content = strip_tags(html_content)
    email = EmailMultiAlternatives(
        "Order Placed",
        text_content,
        SENDER_EMAIL,
        [order.email]
    )
    email.attach_alternative(html_content, "text/html")
    email.send()


def send_mail_for_refund(email_id, order, t):
    req_time = datetime.strftime(t, '%d-%m-%y %H:%M:%s')
    context = {
        'order': order,
        'req_time': req_time
    }
    html_content = render_to_string("confirmations/refund_mail_to_iara_gmail.html", context)
    text_content = strip_tags(html_content)
    email = EmailMultiAlternatives(
        "Refund Requested",
        text_content,
        SENDER_EMAIL,
        [email_id,]
    )
    email.attach_alternative(html_content, "text/html")
    email.send()


@csrf_exempt
def payment_success(request):
    if request.GET.get('q'):
        search = request.GET.get('q')
        return redirect('/search-result/' + search)
    if request.method == 'POST':
        rp_details = request.POST
        print(rp_details)
        try:
            order = Order.objects.get(user=request.user, ordered=False)
        except:
            return redirect('my-orders')
        check = client.utility.verify_payment_signature(rp_details)
        print(check)
        if not check:
            amount = int(order.get_total())
            payment = Payment()
            payment.user = request.user
            payment.amount = order.get_total()
            payment.rp_order_id = rp_details['razorpay_order_id']
            payment.rp_payment_id = rp_details['razorpay_payment_id']
            payment.save()

            # assign the payment to the order
            order.ordered = True
            order.rp_payment_id = rp_details['razorpay_payment_id']
            order.payment = payment
            order.ordered_date = timezone.now()
            order.save()

            send_mail_to_buyer(order)
            # assign the payment to the order_items
            order_items = order.items.all()
            order_items.update(ordered=True)
            order_items.update(rp_payment_id=rp_details['razorpay_payment_id'])
            for item in order_items:
                item.save()

            # creating sellers sale instance
            seller_items={}
            for item in order.items.all():
                seller = item.item.seller
                if seller in seller_items.keys():
                    seller_items[seller].append(item)
                else:
                    seller_items[seller] = [item]
            
            for seller in seller_items.keys():
                sellersale = SellerSale.objects.create(seller=seller, order=order)
                for item in seller_items[seller]:
                    sellersale.items.add(item)
                sellersale.payment = payment
                sellersale.order = order
                sellersale.save()
                send_mail_to_seller(sellersale)

            context = {
                'order': order
            }
            messages.success(request, "Payment Successful!")
            return redirect("/order-placed/" + rp_details['razorpay_payment_id'])
        else:
            messages.success(request, "Payment Unsuccessful!")
            return redirect("/checkout")
    return redirect("/my-orders")

def order_placed(request, payment_id):
    if request.GET.get('q'):
        search = request.GET.get('q')
        return redirect('/search-result/' + search)
    order = Order.objects.get(user=request.user, rp_payment_id=payment_id)
    can_request_for_refund = False
    curr_time = timezone.now()
    order_time = order.payment.timestamp
    if (curr_time < (order_time + timezone.timedelta(hours=48))):
        can_request_for_refund = True
    context = {
        'order': order,
        'can_request_for_refund': can_request_for_refund
    }
    return render(request, "bookstore/order_placed.html", context)




def request_refund(request, payment_id):
    order = Order.objects.get(user=request.user, rp_payment_id=payment_id)
    curr_time = timezone.now()
    order_time = order.payment.timestamp
    if (curr_time < (order_time + timezone.timedelta(hours=48))):
        order.refund_requested = True
        send_mail_for_refund('info.iarabooks@gmail.com', order, curr_time)
        return redirect("order-placed", payment_id=payment_id)
        messages.info(request, "Refund requested for this order!")
    else:
        return redirect("order-placed", payment_id=payment_id)
        messages.warning(request, "You cannot request for refund now!")

def grant_refund(request, payment_id):
    order = Order.objects.get(user=request.user, rp_payment_id=payment_id)
    order.refund_granted = True
    messages.info(request, "Refund granted!")

@login_required
def my_orders(request):
    if request.GET.get('q'):
        search = request.GET.get('q')
        return redirect('/search-result/' + search)
    orders = Order.objects.filter(user=request.user).order_by("-ordered_date")
    context = {
        'orders': orders
    }
    return render(request, 'bookstore/my_orders.html', context)


@login_required
def seller_sale(request):
    seller = Seller.objects.get(user=request.user)
    my_sale = SellerSale.objects.filter(seller=seller)
    context = {
        'my_sale': my_sale
    }
    return render(request, "bookstore/seller_sale_history.html", context)


@login_required
def seller_order_details(request, payment_id):
    payment = Payment.objects.get(rp_payment_id=payment_id)
    seller_order_details = SellerSale.objects.get(payment=payment)
    context = {
        'seller_order_details': seller_order_details
    }
    return render(request, "bookstore/seller_order_details.html", context)

def search_result(request, search):
    context = {}
    all_books = get_book_queryset(search)
    

    all_books_p = Paginator(all_books, 10)
    page = request.GET.get('page')
    all_books = all_books_p.get_page(page)

    context['books'] = all_books

    return render(request, 'bookstore/book_list.html', context)



class AddReferalView(View):
    def post(self, *args, **kwargs):
        form = ReferalForm(self.request.POST or None)
        if form.is_valid():
            try:
                code = form.cleaned_data.get('rcode')
                codes = Seller.objects.values_list('ref_code', flat=True).distinct()
                if code in codes:
                    order = Order.objects.get(
                        user=self.request.user, ordered=False)
                    order.referal = Seller.objects.get(ref_code=code)
                    order.save()
                    messages.success(self.request, "Successfully added referal code!")
                    return redirect("checkout")
                else:
                    messages.info(self.request, "Invalid code!")
                    return redirect("checkout")
            except ObjectDoesNotExist:
                messages.info(self.request, "You do not have an active order!")
                return redirect("checkout")
            except ValueError:
                messages.info(self.request, "Invalid code!")
                return redirect("checkout")

@login_required
def activate_sellers_account(request):
    try:
        curr_seller = Seller.objects.get(user=request.user)
        if request.method == 'POST':
            form = ActivateSellerForm(request.POST)
            if form.is_valid():
                code = form.cleaned_data.get('ref_code')
                if curr_seller.ref_code == code:
                    curr_seller.is_active = True
                    curr_seller.save()
                    messages.info(request, "Congratulations!! You are now a seller. You can now add books for sale.")
                    return redirect('/')
                else:
                    messages.warning(request, "Wrong code!")
                    return redirect('/activate-sellers-account')
            else:
                messages.warning(request, "Invalid Code")
                return redirect("/activate-sellers-account")
        
        else:
            form = ActivateSellerForm()
            context = {
                'form': form
            }
            return render(request, 'bookstore/activate_sellers_account.html', context)
    except:
        messages.warning(request, "You don't have a seller account yet.")
        return redirect('/add-seller')
                



def tagged(request, slug):
    tag = get_object_or_404(Tag, slug=slug)
    # filter Books by tag names
    books = Book.objects.filter(tags=tag)
    context = {
        'tag': tag,
        'books': books
    }
    return render(request, 'bookstore/book_list.html', context)

def terms_and_conditions(request):
    return render(request, 'bookstore/terms_and_conditions.html')

def about_us(request):
    return render(request, 'bookstore/about_us.html')

def privacy(request):
    return render(request, 'bookstore/privacy.html')

def refunds_cancellation(request):
    return render(request, 'bookstore/refunds_cancellation.html')
