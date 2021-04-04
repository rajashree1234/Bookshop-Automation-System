from django import forms
from django_countries.fields import CountryField
from django_countries.widgets import CountrySelectWidget
from .models import Book, Seller, User

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


class CheckoutForm(forms.Form):
    shipping_address = forms.CharField(required=True)
    shipping_address2 = forms.CharField(required=False)
    shipping_country = CountryField(blank_label='(select country)').formfield(
        required=True,
        widget=CountrySelectWidget(attrs={
            'class': 'custom-select d-block w-100',
        }))
    shipping_zip = forms.CharField(required=True)

    billing_address = forms.CharField(required=True)
    billing_address2 = forms.CharField(required=False)
    billing_country = CountryField(blank_label='(select country)').formfield(
        required=True,
        widget=CountrySelectWidget(attrs={
            'class': 'custom-select d-block w-100',
        }))
    billing_zip = forms.CharField(required=True)

    bstate = forms.CharField(required=True)
    bcity = forms.CharField(required=True)
    bdistrict = forms.CharField(required=True)
    sstate = forms.CharField(required=True)
    scity = forms.CharField(required=True)
    sdistrict = forms.CharField(required=True)
    firstname = forms.CharField(required=True)
    lastname = forms.CharField(required=True)
    email = forms.EmailField(required=True)
    phone_number = forms.IntegerField(required=True)

    same_billing_address = forms.BooleanField(required=False)
    set_default_shipping = forms.BooleanField(required=False)
    use_default_shipping = forms.BooleanField(required=False)
    set_default_billing = forms.BooleanField(required=False)
    use_default_billing = forms.BooleanField(required=False)

    # payment_option = forms.ChoiceField(
    #     widget=forms.RadioSelect, choices=PAYMENT_CHOICES)


class CouponForm(forms.Form):
    code = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Promo code',
        'aria-label': 'Recipient\'s username',
        'aria-describedby': 'basic-addon2'
    }))

class ReferalForm(forms.Form):
    rcode = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Referal Code',
        'aria-label': 'Recipient\'s username',
        'aria-describedby': 'basic-addon2'
    }))


class RefundForm(forms.Form):
    ref_code = forms.CharField()
    message = forms.CharField(widget=forms.Textarea(attrs={
        'rows': 4
    }))
    email = forms.EmailField()


class PaymentForm(forms.Form):
    stripeToken = forms.CharField(required=False)
    save = forms.BooleanField(required=False)
    use_default = forms.BooleanField(required=False)


class AddBookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = [
            'title',
            'author',
            'price',
            'discount_price',
            'description',
            'category',
            'language',
            'tags',
            'image',
            'weight',
        ]

class AddSellerForm(forms.Form):
    phone_number = forms.IntegerField()

class BookUpdateForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = [
            'title',
            'author',
            'price',
            'discount_price',
            'description',
            'category',
            'language',
            'tags',
            'image',
            'weight',
        ]


class UserUpdateForm(forms.Form):
    username = forms.CharField()
    first_name = forms.CharField()
    last_name = forms.CharField()
    email = forms.EmailField()

class ActivateSellerForm(forms.Form):
    ref_code = forms.CharField()