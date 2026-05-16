import random
from io import BytesIO
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.core.files.base import ContentFile
from django.core.validators import RegexValidator, URLValidator
from django.core.exceptions import ValidationError
from PIL import Image, ImageDraw, ImageFont

def validate_github_url(value):
    validator = URLValidator()
    validator(value)
    if 'github.com' not in value:
        raise ValidationError('Ссылка должна вести на GitHub')

class UserManager(BaseUserManager):
    def create_user(self, email, name, surname, password=None, **extra_fields):
        if not email:
            raise ValueError('Email обязателен')
        email = self.normalize_email(email)
        user = self.model(email=email, name=name, surname=surname, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, surname, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        return self.create_user(email, name, surname, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True, verbose_name='Email')
    name = models.CharField(max_length=124, verbose_name='Имя')
    surname = models.CharField(max_length=124, verbose_name='Фамилия')
    avatar = models.ImageField(upload_to='avatars/', default='avatars/default.png', verbose_name='Аватар')
    phone = models.CharField(
        max_length=12,
        unique=True,
        validators=[RegexValidator(r'^\+7\d{10}$', 'Телефон должен быть в формате +7XXXXXXXXXX')],
        verbose_name='Телефон'
    )
    github_url = models.URLField(blank=True, validators=[validate_github_url], verbose_name='GitHub')
    about = models.TextField(max_length=256, blank=True, verbose_name='О себе')
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    favorites = models.ManyToManyField('projects.Project', related_name='interested_users', blank=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name', 'surname']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return f'{self.name} {self.surname}'

    def get_full_name(self):
        return f'{self.name} {self.surname}'

    def generate_avatar(self):
        colors = [
            '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
            '#DDA0DD', '#98D8C8', '#F7B731', '#5D9B9B', '#E76F51'
        ]
        bg_color = random.choice(colors)
        first_letter = self.name[0].upper() if self.name else '?'
        
        size = 200
        image = Image.new('RGB', (size, size), bg_color)
        draw = ImageDraw.Draw(image)
        
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 120)
        except:
            font = ImageFont.load_default()
        
        bbox = draw.textbbox((0, 0), first_letter, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (size - text_width) // 2
        y = (size - text_height) // 2
        
        draw.text((x, y), first_letter, fill='#FFFFFF', font=font)
        
        buffer = BytesIO()
        image.save(buffer, format='PNG')
        filename = f'avatar_{self.id}.png' if self.id else f'avatar_temp.png'
        self.avatar.save(filename, ContentFile(buffer.getvalue()), save=False)

    def save(self, *args, **kwargs):
        is_new = not self.pk
        super().save(*args, **kwargs)
        if is_new:
            self.generate_avatar()
            super().save(update_fields=['avatar'])