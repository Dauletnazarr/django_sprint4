from django.urls import path, include

from . import views

app_name = 'blog'

urlpatterns = [
    path('auth/', include('django.contrib.auth.urls')),
    path('posts/create/', views.PostCreateView.as_view(), name='create_post'),
    path('', views.IndexView.as_view(), name='index'),
    path('posts/<int:post_id>/', views.PostDetailView.as_view(), name='post_detail'),
    path('category/<slug:category_slug>/', views.CategoryPostsView.as_view(), name='category_posts'),
    path('posts/<int:post_id>/edit/', views.PostUpdateView.as_view(), name='edit_post'),
    path('posts/<int:post_id>/delete/', views.PostDeleteView.as_view(
    ), name='delete_post'),
    path('posts/<int:pk>/comment/', views.add_comment, name='add_comment'),
    path(
        'posts/<int:post_id>/delete_comment/<int:pk>', views.CommentDeleteView.as_view(
    ), name='delete_comment'),
    path(
        'posts/<int:post_id>/edit_comment/<int:pk>', views.CommentUpdateView.as_view(
    ), name='edit_comment'),
    path(
        'profile/edit/', views.UserEditView.as_view(), name='edit_profile'
    ),
    path(
        'profile/<str:username>/', views.UserProfileView.as_view(), name='profile'
    ),
]
