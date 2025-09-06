from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate

from .models import Category, Post


class ContactForm(forms.Form):
    name = forms.CharField(label='Name', max_length=100, required=True)
    email = forms.EmailField(label='Email', required=True)
    message = forms.CharField(label='Message', required=True)


from django.core.exceptions import ValidationError

class RegisterForm(forms.ModelForm):
    username = forms.CharField(label='username', max_length=100, required=True)
    email = forms.EmailField(label="email", max_length=100, required=True)
    password = forms.CharField(label="password", max_length=100, required=True)
    password_confirm = forms.CharField(label="password_confirm", max_length=100, required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    # Add this method to check if username exists
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError("This username is already taken. Please choose another.")
        return username

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')

        if password and password_confirm and password != password_confirm:
            raise ValidationError("Passwords do not match.")
        return cleaned_data

    

class LoginForm(forms.Form):
    username = forms.CharField(label='username', max_length=100, required=True)
    password = forms.CharField(label='password', max_length=100, required=True)


    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username') 
        password = cleaned_data.get('password') 
        if username and password: 
            user = authenticate(username=username,password=password)
            if user is None:
                raise forms.ValidationError('Invalid username and password')
        return cleaned_data
    

class ForgotPasswordForm(forms.Form):
    email = forms.EmailField(label='Email', max_length=254, required=True)

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')

        if not User.objects.filter(email=email).exists():
            raise forms.ValidationError("No User Registered with this email.")
        

class ResetPasswordForm(forms.Form):
    new_password = forms.CharField(label='New Password', min_length=8)
    confirm_password = forms.CharField(label='Confirm Password', min_length=8)

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get("new_password")
        confirm_password = cleaned_data.get("confirm_password")

        if new_password and confirm_password and new_password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")
        

class PostForm(forms.ModelForm):
    title = forms.CharField(label='Title', max_length=200, required=True)
    content = forms.CharField(label='Content', required=True)
    category = forms.ModelChoiceField(label='Category',queryset=Category.objects.all(),required=True)
    img_url = forms.ImageField(label='Image', required=False)

    class Meta:
        model = Post
        fields =['title','content','category','img_url']

    def clean(self):
        cleaned_data = super().clean()
        title = cleaned_data.get('title')
        content = cleaned_data.get('content')

        #custom validation

        if title and len(title)<5:
            raise forms.ValidationError('Blog Title must be atleast 5 Characters')

        if content and len(content)<5:
            raise forms.ValidationError('Blog Content must be atleast 10 Characters')
        
    def save(self, commit = ...):

        post =  super().save(commit)
        cleaned_data = super().clean()

        if cleaned_data.get('img_url'):
            post.img_url = cleaned_data.get('img_url')
        else:
            img_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ac/No_image_available.svg/600px-No_image_available.svg.png"
            post.img_url = img_url

        if commit:
            post.save()
        return post


