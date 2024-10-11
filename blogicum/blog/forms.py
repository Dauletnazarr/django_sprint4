from django import forms

# Импортируем класс модели Birthday.
from .models import Post, Comment

from django.core.mail import send_mail


class PostForm(forms.ModelForm):

    class Meta:
        model = Post
        exclude = ('author',)
        fields = '__all__'
        widgets = {
            'pub_date': forms.DateTimeInput(
                attrs={'type': 'date'}),
        }


class CommentForm(forms.ModelForm):

    class Meta:
        model = Comment
        fields = ('text',)

    def clean(self):
        super().clean()
        text = self.cleaned_data['text']
        send_mail(
            subject='Another Beatles member',
            message=f'{text} пытался написать коммент!',
            from_email='birthday_form@acme.not',
            recipient_list=['admin@acme.not'],
            fail_silently=True,
        )
