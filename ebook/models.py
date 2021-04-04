from django.db import models
from django.db.models.signals import post_save
from django.utils import timezone
from django.contrib.auth.models import User
from django_countries.fields import CountryField
from django.shortcuts import reverse
from taggit.managers import TaggableManager


CATEGORY_CHOICES = (
    ('Historical', 'Historical'),
    ('Horror', 'Horror'),
    ('Romance', 'Romance'),
    ('Suspense','Suspense'),
)

LANGUAGES = {
    ('English', 'English'),  
}

ADDRESS_CHOICES = (
    ('B', 'Billing'),
    ('S', 'Shipping'),
)

SIDE_PANEL_POSITION_CHOICES = {
    ('first_image', 'first_image'),
    ('second_image', 'second_image'),
    ('yt_video_link', 'yt_video_link'),
}

class CarauselImage(models.Model):
    image = models.ImageField(upload_to='carausel_pics')
    link = models.CharField(max_length=300, null=True)
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return self.link

class SidePanelImages(models.Model):
    image = models.ImageField(upload_to='side_panel_pics', null=True)
    link = models.CharField(max_length=300, null=True)
    position = models.CharField(choices=SIDE_PANEL_POSITION_CHOICES, max_length=60, unique=True)

    def __str__(self):
        return self.position

class UserProfile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE)
    stripe_customer_id = models.CharField(max_length=50, blank=True, null=True)
    one_click_purchasing = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username

class Seller(models.Model):
    user = models.OneToOneField(User, primary_key=True, on_delete=models.CASCADE, related_name='seller_profile')
    is_active = models.BooleanField(default=False)
    phone_number = models.CharField(max_length=15)
    # account_number = models.IntegerField()
    ref_code = models.CharField(max_length=10)

    def __str__(self):
        return self.user.username

def has_sellers_account(self):
    try:
        if Seller.objects.get(user=self):
            return True
        else:
            return False
    except:
        return False

def is_seller(self):
    try:
        curr_seller =  Seller.objects.get(user=self)
        if curr_seller.is_active:
            return True
        else:
            return False
    except:
        return False

def get_sellers_refcode(self):
    curr_seller = Seller.objects.get(user=self)
    return curr_seller.ref_code

User.add_to_class("is_seller", is_seller)
User.add_to_class("get_sellers_refcode", get_sellers_refcode)
User.add_to_class("has_sellers_account", has_sellers_account)


class Coupon(models.Model):
    code = models.CharField(max_length=15)
    amount = models.FloatField()

    def __str__(self):
        return self.code

class Book(models.Model):
    title = models.CharField(max_length=100)
    author = models.CharField(max_length=500)
    price = models.FloatField()
    discount_price = models.FloatField(blank=True, null=True, default=40.0)
    description = models.TextField()
    weight = models.FloatField(default=200)

    category = models.CharField(choices=CATEGORY_CHOICES, max_length=60, default='History - Târeekh')
    language = models.CharField(choices=LANGUAGES, max_length=8, default='Urdu')
    tags = TaggableManager()

    slug = models.SlugField(unique=True, max_length=100)
    date_posted = models.DateTimeField(default=timezone.now)
    image = models.ImageField(upload_to='cover_pics', default='default.jpg')
    seller = models.ForeignKey(Seller, on_delete=models.CASCADE, default=2)
    

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("product-detail", kwargs={
            'slug': self.slug
        })
    
    def actual_price(self):
        return self.price - (self.price * self.discount_price)/100

    def get_add_to_cart_url(self):
        return reverse("add-to-cart", kwargs={
            'slug': self.slug
        })

    def get_remove_from_cart_url(self):
        return reverse("remove-from-cart", kwargs={
            'slug': self.slug
        })

    def get_add_to_wishlist_url(self):
        return reverse("add-to-wishlist", kwargs={
            'slug': self.slug
        })

    def get_remove_from_wishlist_url(self):
        return reverse("remove-from-wishlist", kwargs={
            'slug': self.slug
        })
    
    def get_author_length(self):
        return len(self.author)

    def get_tags_list(self):
        tag_list = self.get_tags_display().split(',')
        return tag_list

    def get_updating_url(self):
        return reverse("update-book", kwargs={
            'slug': self.slug
        })
    
    # def get_deleting_url(self):
    #     return reverse("delete-book", kwargs={
    #         'slug': self.slug
    #     })

class OrderItem(models.Model):
    user = models.ForeignKey(User, 
    on_delete=models.CASCADE)
    ordered = models.BooleanField(default=False)
    item = models.ForeignKey(Book, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)

    rp_order_id = models.CharField(max_length=20, blank=True, null=True)
    rp_payment_id = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return f"{self.quantity} of {self.item.title}"

    def get_total_item_price(self):
        return self.quantity * self.item.price

    def get_total_discount_item_price(self):
        return self.get_total_item_price() - (self.quantity * self.item.discount_price * self.item.price / 100)

    def get_amount_saved(self):
        return self.quantity * self.item.discount_price * self.item.price / 100

    def get_final_price(self):
        if self.item.discount_price:
            return self.get_total_discount_item_price()
        return self.get_total_item_price()

    def get_total_weight(self):
        return self.quantity * self.item.weight

class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    items = models.ManyToManyField(Book)

    def __str__(self):
        return self.user.username

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    firstname = models.CharField(max_length=100, null=True)
    lastname = models.CharField(max_length=100, null=True)
    email = models.EmailField(max_length=100, null=True)
    phone_number = models.CharField(max_length=15, null=True)

    rp_order_id = models.CharField(max_length=20, blank=True, null=True)
    rp_payment_id = models.CharField(max_length=20, blank=True, null=True)

    items = models.ManyToManyField(OrderItem)
    start_date = models.DateTimeField(auto_now_add=True)
    ordered_date = models.DateTimeField(null=True)
    ordered = models.BooleanField(default=False)
    shipping_address = models.ForeignKey(
        'Address', related_name='shipping_address', on_delete=models.SET_NULL, blank=True, null=True)
    billing_address = models.ForeignKey(
        'Address', related_name='billing_address', on_delete=models.SET_NULL, blank=True, null=True)
    payment = models.ForeignKey(
        'Payment', on_delete=models.SET_NULL, blank=True, null=True)
    coupon = models.ForeignKey('Coupon', on_delete=models.SET_NULL, blank=True, null=True)
    referal = models.ForeignKey('Seller', on_delete=models.SET_NULL, blank=True, null=True)
    being_delivered = models.BooleanField(default=False)
    received = models.BooleanField(default=False)
    refund_requested = models.BooleanField(default=False)
    refund_granted = models.BooleanField(default=False)

    '''
    1. Item added to cart
    2. Adding a billing address
    (Failed checkout)
    3. Payment
    (Preprocessing, processing, packaging etc.)
    4. Being delivered
    5. Received
    6. Refunds
    '''

    def __str__(self):
        return self.user.username

    def is_payment_pending(self):
        if self.rp_order_id:
            if self.rp_payment_id:
                return False
            else:
                return True
        else:
            False

    def get_total_weight(self):
        total = 0
        for order_item in self.items.all():
            total += order_item.get_total_weight()
        return total
    
    def get_weight_price(self):
        tw = self.get_total_weight()
        if tw == 0:
            return 0
        if tw <= 200:
            return 25
        elif tw>200 and tw<=500:
            return 50
        else:
            tw = tw/1000
            if tw%5:
                return 100*(int(tw/5) + 1)
            else:
                return 100*(int(tw/5))

    def get_total(self):
        total = 0
        for order_item in self.items.all():
            total = total + order_item.get_final_price()
        total = total + self.get_weight_price()
        if self.coupon:
            total -= self.coupon.amount
        return total
    
    def get_total_quantity(self):
        total = 0
        for order_item in self.items.all():
            total += order_item.quantity
        return total

class Address(models.Model):
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE)
    street_address = models.CharField(max_length=100)
    apartment_address = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    district = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = CountryField(multiple=False)
    zip = models.CharField(max_length=100)
    address_type = models.CharField(max_length=1, choices=ADDRESS_CHOICES)
    default = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username

    class Meta:
        verbose_name_plural = 'Addresses'

class Payment(models.Model):
    rp_payment_id = models.CharField(max_length=20, blank=True, null=True)
    rp_order_id = models.CharField(max_length=20, blank=True, null=True)
    user = models.ForeignKey(User,
                             on_delete=models.SET_NULL, blank=True, null=True)
    amount = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username

class Refund(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    reason = models.TextField()
    accepted = models.BooleanField(default=False)
    email = models.EmailField()

    def __str__(self):
        return f"{self.pk}"

class SellerSale(models.Model):
    seller = models.ForeignKey(Seller, on_delete=models.CASCADE)
    items = models.ManyToManyField(OrderItem)
    payment = models.ForeignKey(
        'Payment', on_delete=models.SET_NULL, null=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE)

    def __str__(self):
        return self.seller.user.username

    def get_sellers_total(self):
        total = 0
        for order_item in self.items.all():
            total += order_item.get_final_price()
        return total