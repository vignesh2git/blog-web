from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse, JsonResponse
from django.urls import reverse
import logging
from django.views.decorators.http import require_POST,require_http_methods,require_GET
from django.views.decorators.csrf import csrf_exempt

from django.http import Http404
from django.core.paginator import Paginator

from .models import Category, Follow, LikePost, Notification, Post, Comment, LikeComment
from .forms import (
    ContactForm,
    ForgotPasswordForm,
    LoginForm,
    PostForm,
    RegisterForm,
    ResetPasswordForm,
)
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout

from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from urllib.parse import urlparse


blog_title = "𝐋𝐚𝐭𝐞𝐬𝐭 𝐏𝐨𝐬𝐭𝐬 "


# Create your views here.
def index(request):

    # getting data from Post model
    posts = Post.objects.order_by("id")[:3]

    liked_post_ids = []
    if request.user.is_authenticated:
        liked_post_ids = LikePost.objects.filter(
            username=request.user.username
        ).values_list("post_id", flat=True)
    return render(
        request,
        "index.html",
        {"blog_title": blog_title, "posts": posts, "liked_post_ids": liked_post_ids},
    )

@login_required
def blog_post_page(request):

    # getting data from Post model
    all_posts = Post.objects.filter(is_published=True)

    # paginate
    paginator = Paginator(all_posts, 9)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    liked_post_ids = []
    if request.user.is_authenticated:
        liked_post_ids = LikePost.objects.filter(
            username=request.user.username
        ).values_list("post_id", flat=True)
    return render(
        request,
        "latest_post.html",
        {
            "blog_title": blog_title,
            "page_obj": page_obj,
            "liked_post_ids": liked_post_ids,
        },
    )


def detail(request, slug):

    if not request.user.is_authenticated:
        messages.error(
            request, "You must be logged in to view the full post. Please Login...!"
        )
        return redirect("blog:index")

    try:
        # getting data from model by post id
        post = Post.objects.get(slug=slug)
        related_posts = Post.objects.filter(category=post.category).exclude(pk=post.id)

    except Post.DoesNotExist:
        raise Http404("Post Does not Exist")

    liked = False
    if request.user.is_authenticated:
        liked = LikePost.objects.filter(
            post=post, username=request.user.username
        ).exists()
    is_own_profile = request.user == post.user
    profile_user = post.user
    is_following = False

    if request.user.is_authenticated and not is_own_profile:
        is_following = Follow.objects.filter(
            follower=request.user, following=profile_user
        ).exists()

        # BACK BUTTON LOGIC
    referer = request.META.get("HTTP_REFERER", "")
    referer_path = urlparse(referer).path

    if referer_path == reverse("blog:dashboard"):
        back_label = "Back to Dashboard"
        back_url = reverse("blog:dashboard")
    else:
        back_label = "Back to Posts"
        back_url = reverse("blog:blog_post_page")

    return render(
        request,
        "detail.html",
        {
            "post": post,
            "related_posts": related_posts,
            "liked": liked,
            "back_label": back_label,
            "is_own_profile": is_own_profile,
            "profile_user": profile_user,
            "is_following": is_following,
            "back_url": back_url,
        },
    )





def contact(request):
    if request.method == "POST":
        form = ContactForm(request.POST)
        name = request.POST.get("name")
        email = request.POST.get("email")
        message = request.POST.get("message")

        logger = logging.getLogger("test mode")
        if form.is_valid():
            logger.debug(
                f"post Data is {form.cleaned_data['name']},{form.cleaned_data['email']},{form.cleaned_data['message']}"
            )
            # send email 
            messages.success(request, "Your password has been reset successfully!")
            return render(request, "contact.html", {"form": form})

        else:
            logger.debug("Form validation Failed")
            return render(
                request,
                "contact.html",
                {"form": form, "name": name, "email": email, "message": message},
            )
    return render(request, "contact.html")


def about(request):
    return render(request, "about.html")


def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data["password"])  
            user.save()
            # add user to readers group
            readers_group, created = Group.objects.get_or_create(name="Readers")
            user.groups.add(readers_group)
            messages.success(request, "Registration successful! You can now log in.")
            return redirect("blog:login")  # Redirect to the login page or another page
    else:
        form = RegisterForm()
    return render(request, "register.html", {"form": form})


def login(request):
    if request.method == "POST":
        # login form
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            user = authenticate(username=username, password=password)
            if user is not None:
                auth_login(request, user)
                return redirect("blog:dashboard")  
    else:
        form = LoginForm()
    return render(request, "login.html", {"form": form})


@login_required
def dashboard(request):

    # getting user posts
    all_posts = Post.objects.filter(user=request.user)

    # Count of all posts for this user
    user_post_count = all_posts.count()
    followers_count = Follow.objects.filter(following=request.user).count()
    following_count = Follow.objects.filter(follower=request.user).count()
    liked_post_ids = []
    if request.user.is_authenticated:
        liked_post_ids = LikePost.objects.filter(
            username=request.user.username
        ).values_list("post_id", flat=True)

    notifications = Notification.objects.filter(recipient=request.user).order_by(
        "-created_at"
    )[:10]
    has_unread_notifications = Notification.objects.filter(
        recipient=request.user, is_read=False
    ).exists()

    return render(
        request,
        "dashboard.html",
        {
            "all_posts": all_posts,
            "liked_post_ids": liked_post_ids,
            "followers_count": followers_count,
            "following_count": following_count,
            "user_post_count": user_post_count,
            "notifications": notifications,
            "has_unread_notifications": has_unread_notifications,
        },
    )


@login_required
def settings(request):
    profile = request.user.profile

    if request.method == "POST":
        new_username = request.POST.get("username") or request.user.username
        new_email = request.POST.get("email") or request.user.email
        new_bio = request.POST.get("bio") or profile.bio
        profile_image = request.FILES.get("profileImage")

        request.user.username = new_username
        request.user.email = new_email
        request.user.save()

        profile.bio = new_bio
        if profile_image:
            profile.profile_image = profile_image
        profile.save()

        messages.success(request, "Profile updated successfully!")
        return redirect("blog:settings")

    return render(request, "setting.html")





@login_required
def user_profile(request, username):
    target_user = get_object_or_404(User, username=username)

    if request.user == target_user:
        return redirect("blog:profile")

    posts = Post.objects.filter(user=target_user, is_published=True)
    liked_post_ids = []
    if request.user.is_authenticated:
        liked_post_ids = LikePost.objects.filter(
            username=request.user.username
        ).values_list("post_id", flat=True)
    is_following = Follow.objects.filter(
        follower=request.user, following=target_user
    ).exists()
    followers_count = Follow.objects.filter(following=target_user).count()
    following_count = Follow.objects.filter(follower=target_user).count()

    referer = request.META.get("HTTP_REFERER", "")
    referer_path = urlparse(referer).path

    if referer_path == reverse("blog:dashboard"):
        back_label = "Back to Dashboard"
        back_url = reverse("blog:dashboard")
    else:
        back_label = "Back to Posts"
        back_url = reverse("blog:blog_post_page")

    return render(
        request,
        "profile.html",
        {
            "profile_user": target_user,
            "all_posts": posts,
            "liked_post_ids": liked_post_ids,
            "is_following": is_following,
            "followers_count": followers_count,
            "following_count": following_count,
            "is_own_profile": False,  
            "back_label": back_label,
            "back_url": back_url,
        },
    )


@login_required
def profile(request):
    # getting user posts
    all_posts = Post.objects.filter(user=request.user)

    #  Count of all posts for this user
    user_post_count = all_posts.count()
    followers_count = Follow.objects.filter(following=request.user).count()
    following_count = Follow.objects.filter(follower=request.user).count()
    liked_post_ids = []
    if request.user.is_authenticated:
        liked_post_ids = LikePost.objects.filter(
            username=request.user.username
        ).values_list("post_id", flat=True)

    return render(
        request,
        "profile.html",
        {
            "all_posts": all_posts,
            "liked_post_ids": liked_post_ids,
            "user_post_count": user_post_count,
            "followers_count": followers_count,
            "following_count": following_count,
            "is_own_profile": True,
        },
    )


@login_required
@csrf_exempt 
def toggle_follow(request):
    if request.method == "POST":
        username_to_follow = request.POST.get("username")
        if not username_to_follow:
            return JsonResponse({"success": False, "error": "No username provided."})

        user_to_follow = get_object_or_404(User, username=username_to_follow)

        # Prevent users from following themselves
        if user_to_follow == request.user:
            return JsonResponse(
                {"success": False, "error": "You cannot follow yourself."}
            )

        follow_obj, created = Follow.objects.get_or_create(
            follower=request.user, following=user_to_follow
        )

        if not created:
            # already following, so unfollow
            follow_obj.delete()
            is_following = False
        else:
            is_following = True

            if user_to_follow != request.user:
                Notification.objects.create(
                    recipient=user_to_follow, sender=request.user, type="follow"
                )

        # Return updated follower/following count
        followers_count = Follow.objects.filter(following=user_to_follow).count()
        following_count = Follow.objects.filter(follower=user_to_follow).count()

        return JsonResponse(
            {
                "success": True,
                "is_following": is_following,
                "followers_count": followers_count,
                "following_count": following_count,
            }
        )
    else:
        return JsonResponse({"success": False, "error": "Invalid request method."})


@login_required
@require_POST
def update_bio(request):
    new_bio = request.POST.get("bio")
    profile = request.user.profile

    if new_bio is not None:
        profile.bio = new_bio
        profile.save()
        messages.success(request, "Bio updated successfully!")

    return redirect("blog:settings")



def logout(request):
    auth_logout(request)
    return redirect("blog:index")


def forgot_password(request):
    form = ForgotPasswordForm()
    if request.method == "POST":
        # form
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            user = User.objects.get(email=email)
            # send email to reset password
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            current_site = get_current_site(request)
            domain = current_site.domain
            subject = "Reset Password Requested"
            message = render_to_string(
                "reset_password_email.html",
                {"domain": domain, "uid": uid, "token": token},
            )

            send_mail(subject, message, "noreply@vc.com", [email])
            messages.success(request, "Email has been sent")

    return render(request, "forgot_password.html", {"form": form})


def reset_password(request, uidb64, token):
    form = ResetPasswordForm()
    if request.method == "POST":
        # form
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            new_password = form.cleaned_data["new_password"]
            try:
                uid = urlsafe_base64_decode(uidb64)
                user = User.objects.get(pk=uid)
            except (TypeError, ValueError, OverflowError, User.DoesNotExist):
                user = None

            if user is not None and default_token_generator.check_token(user, token):
                user.set_password(new_password)
                user.save()
                messages.success(request, "Your password has been reset successfully!")
                return redirect("blog:login")
            else:
                messages.error(request, "The password reset link is invalid")

    return render(request, "reset_password.html", {"form": form})


@login_required
def new_post(request):
    categories = Category.objects.all()
    form = PostForm()
    if request.method == "POST":
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.user = request.user
            post.save()
            return redirect("blog:dashboard")
    return render(request, "new_post.html", {"categories": categories, "form": form})


@login_required
def edit_post(request, post_id):
    categories = Category.objects.all()
    post = get_object_or_404(Post, id=post_id)
    form = PostForm()
    if request.method == "POST":
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            messages.success(request, "Post Updated successfully!")
            return redirect("blog:dashboard")

    return render(
        request,
        "edit_post.html",
        {"categories": categories, "post": post, "form": form},
    )


@login_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    post.delete()
    messages.success(request, "Post Deleted successfully!")
    return redirect("blog:dashboard")


@login_required
def publish_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    post.is_published = True
    post.save()
    messages.success(request, "Post Published successfully!")
    return redirect("blog:dashboard")


@login_required
@require_POST
def like_post(request):

    post_id = request.POST.get("post_id")
    post = get_object_or_404(Post, id=post_id)
    username = request.user.username

    liked = LikePost.objects.filter(post=post, username=username).first()

    if liked:
        liked.delete()
        post.no_of_likes -= 1
        liked_status = False
    else:
        LikePost.objects.create(post=post, username=username)
        post.no_of_likes += 1
        liked_status = True

        if post.user != request.user:
            Notification.objects.create(
                recipient=post.user, sender=request.user, post=post, type="like"
            )

    post.save()

    return JsonResponse({"liked": liked_status, "like_count": post.no_of_likes})


@login_required
@require_POST
def post_comment(request):
    post_id = request.POST.get("post_id")
    content = request.POST.get("content")
    parent_id = request.POST.get("parent_id")  

    post = get_object_or_404(Post, id=post_id)
    parent_comment = None
    if parent_id:
        parent_comment = get_object_or_404(Comment, id=parent_id)

    comment = Comment.objects.create(
        post=post, user=request.user, content=content, parent=parent_comment
    )

    if post.user != request.user:
        Notification.objects.create(
            recipient=post.user,
            sender=request.user,
            post=post,
            comment=comment,
            type="comment",
        )

    #  Avatar logic for CURRENT USER 
    profile = getattr(request.user, "profile", None)
    if (
        profile
        and profile.profile_image
        and profile.profile_image.url != "/Proflie/images/default.png"
    ):
        avatar_url = profile.profile_image.url
    else:
        avatar_url = f"https://ui-avatars.com/api/?name={request.user.username}&background=random"

    return JsonResponse(
        {
            "success": True,
            "comment_id": comment.id,
            "avatar": avatar_url,
            "username": request.user.username,
            "content": comment.content,
            "created_at": comment.created_at.isoformat(),
            "parent_id": parent_id or "",
            "no_of_likes": comment.no_of_likes,
        }
    )


@login_required
@require_POST
def like_comment(request):
    comment_id = request.POST.get("comment_id")
    comment = get_object_or_404(Comment, id=comment_id)
    username = request.user.username

    liked = LikeComment.objects.filter(comment=comment, username=username).first()

    if liked:
        liked.delete()
        comment.no_of_likes -= 1
        liked_status = False
    else:
        LikeComment.objects.create(comment=comment, username=username)
        comment.no_of_likes += 1
        liked_status = True

        if comment.user != request.user:
            Notification.objects.create(
                recipient=comment.user,
                sender=request.user,
                comment=comment,
                type="comment_like",
            )

    comment.save()

    return JsonResponse({"liked": liked_status, "like_count": comment.no_of_likes})




@login_required
@require_GET
def get_comments(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    comments = post.comments.filter(parent=None).order_by(
        "-created_at"
    )  

    def serialize_comment(comment, request):
        profile = getattr(comment.user, "profile", None)

        if (
            profile
            and profile.profile_image
            and profile.profile_image.url != "/Proflie/images/default.png"
        ):
            avatar_url = profile.profile_image.url
        else:
            avatar_url = f"https://ui-avatars.com/api/?name={comment.user.username}&background=random"

        return {
            "id": comment.id,
            "avatar": avatar_url,
            "username": comment.user.username,
            "content": comment.content,
            "created_at": comment.created_at.isoformat(),
            "no_of_likes": comment.no_of_likes,
            "replies": [
                serialize_comment(reply, request)
                for reply in comment.replies.all().order_by("created_at")
            ],
            "can_delete": comment.user == request.user,
            "liked_by_user": LikeComment.objects.filter(
                comment=comment, username=request.user.username
            ).exists(),
        }

    comment_data = [serialize_comment(c, request) for c in comments]

    return JsonResponse({"comments": comment_data})




@login_required
@require_http_methods(["POST"])
def delete_comment(request):
    comment_id = request.POST.get("comment_id")
    comment = get_object_or_404(
        Comment, id=comment_id, user=request.user
    )  
    comment.delete()
    return JsonResponse({"success": True})


@login_required
@require_POST
def clear_notifications(request):
    user = request.user
    # Assuming your Notification model has a user or recipient field
    user.notifications.all().delete()
    return JsonResponse({"success": True})


@login_required
@require_POST
@csrf_exempt  
def mark_notifications_read(request):
    Notification.objects.filter(recipient=request.user, is_read=False).update(
        is_read=True
    )
    return JsonResponse({"success": True})
