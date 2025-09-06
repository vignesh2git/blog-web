from django.urls import path
from . import views

app_name='blog'

urlpatterns = [
    path('',views.index, name='index'),
    path('blog_post_page',views.blog_post_page, name='blog_post_page'),
    path('post/<str:slug>',views.detail, name='detail'),
    path('contact',views.contact, name='contact'),
    path('about',views.about, name='about'),
    path('register',views.register, name='register'),
    path('login',views.login, name='login'),
    path('dashboard',views.dashboard, name='dashboard'),
    path('settings',views.settings, name='settings'),
    path('profile',views.profile, name='profile'),
    path('profile/<str:username>', views.user_profile, name='user_profile'),
    path('toggle_follow', views.toggle_follow, name='toggle_follow'),
    path('update-bio', views.update_bio, name='update_bio'),
    path('clear_notifications', views.clear_notifications, name='clear_notifications'),
    path('notifications/mark_read/', views.mark_notifications_read, name='mark_notifications_read'),
    path('logout',views.logout, name='logout'),
    path('forgot_password',views.forgot_password, name='forgot_password'),
    path('reset_password/<uidb64>/<token>',views.reset_password, name='reset_password'),
    path('new_post',views.new_post, name='new_post'),
    path('edit_post/<int:post_id>',views.edit_post, name='edit_post'),
    path('delete_post/<int:post_id>',views.delete_post, name='delete_post'),
    path('publish_post/<int:post_id>',views.publish_post, name='publish_post'),
    path('like_post', views.like_post, name='like_post'),
    path('post_comment', views.post_comment, name='post_comment'),
    path('like_comment', views.like_comment, name='like_comment'),
    path('api/comments/<int:post_id>', views.get_comments, name='get_comments'),
    path('delete_comment', views.delete_comment, name='delete_comment'),

]

