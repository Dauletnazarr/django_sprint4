from django.contrib.auth.mixins import UserPassesTestMixin
from django.urls import reverse
from django.shortcuts import get_object_or_404


from blog.models import Comment


class OnlyAuthorMixin(UserPassesTestMixin):

    def test_func(self):
        object = self.get_object()
        return object.author == self.request.user


class CommentMixin(OnlyAuthorMixin):
    template_name = 'blog/comment.html'
    model = Comment
    pk_url_kwarg = 'comment_id'

    def get_success_url(self):
        return reverse(
            'blog:post_detail', kwargs={'post_id': self.kwargs['post_id']}
        )

    def get_object(self, queryset=None):
        comment_id = self.kwargs[self.pk_url_kwarg]
        post_id = self.kwargs['post_id']
        comment = get_object_or_404(
            self.get_queryset(),
            id=comment_id,
            post_id=post_id
        )
        return comment
