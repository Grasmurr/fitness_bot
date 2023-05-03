from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class UnpaidUser(models.Model):
    user_id = models.IntegerField(primary_key=True)
    has_paid = models.BooleanField(default=False)

    def __str__(self):
        return f"id - {self.user_id}"

    class Meta:
        app_label = 'telegram_bot'


class PaidUser(models.Model):
    GENDER_CHOICES = [
        ('M', 'Мужчина'),
        ('F', 'Женщина'),
    ]

    GOAL_CHOICES = [
        ('G', 'Набрать вес'),
        ('L', 'Сбросить вес'),
    ]

    PLACE_CHOICES = [
        ('H', 'Дом'),
        ('G', 'Зал'),
    ]
    LEVEL = [
        ('P', 'Профессиональный'),
        ('N', 'Новичок'),
    ]

    user = models.IntegerField(primary_key=True)
    username = models.CharField(max_length=100, blank=True, null=True)
    full_name = models.CharField(max_length=100, blank=True, null=True)
    paid_day = models.DateField(blank=True, null=True)
    calories = models.IntegerField(blank=True, null=True)
    timezone = models.CharField(max_length=100)
    пол = models.CharField(max_length=7, choices=GENDER_CHOICES, default='M')
    цель = models.CharField(max_length=12, choices=GOAL_CHOICES, default='G')
    место = models.CharField(max_length=3, choices=PLACE_CHOICES, default='H')
    уровень = models.CharField(max_length=16, choices=LEVEL, default='N')

    def __str__(self):
        return f"{self.username} ({self.user})"

    class Meta:
        app_label = 'telegram_bot'


class UserCalories(models.Model):
    user = models.OneToOneField(PaidUser, on_delete=models.CASCADE)
    day1 = models.PositiveIntegerField()
    day1_requested = models.BooleanField(default=False)
    day2 = models.PositiveIntegerField()
    day2_requested = models.BooleanField(default=False)
    day3 = models.PositiveIntegerField()
    day3_requested = models.BooleanField(default=False)
    day4 = models.PositiveIntegerField()
    day4_requested = models.BooleanField(default=False)
    day5 = models.PositiveIntegerField()
    day5_requested = models.BooleanField(default=False)
    day6 = models.PositiveIntegerField()
    day6_requested = models.BooleanField(default=False)
    day7 = models.PositiveIntegerField()
    day7_requested = models.BooleanField(default=False)
    day8 = models.PositiveIntegerField()
    day8_requested = models.BooleanField(default=False)
    day9 = models.PositiveIntegerField()
    day9_requested = models.BooleanField(default=False)
    day10 = models.PositiveIntegerField()
    day10_requested = models.BooleanField(default=False)
    day11 = models.PositiveIntegerField()
    day11_requested = models.BooleanField(default=False)
    day12 = models.PositiveIntegerField()
    day12_requested = models.BooleanField(default=False)
    day13 = models.PositiveIntegerField()
    day13_requested = models.BooleanField(default=False)
    day14 = models.PositiveIntegerField()
    day14_requested = models.BooleanField(default=False)
    day15 = models.PositiveIntegerField()
    day15_requested = models.BooleanField(default=False)
    day16 = models.PositiveIntegerField()
    day16_requested = models.BooleanField(default=False)
    day17 = models.PositiveIntegerField()
    day17_requested = models.BooleanField(default=False)
    day18 = models.PositiveIntegerField()
    day18_requested = models.BooleanField(default=False)
    day19 = models.PositiveIntegerField()
    day19_requested = models.BooleanField(default=False)
    day20 = models.PositiveIntegerField()
    day20_requested = models.BooleanField(default=False)
    day21 = models.PositiveIntegerField()
    day21_requested = models.BooleanField(default=False)

    def __str__(self):
        return f"User {self.user.username} - 21-day calories"


class BankCards(models.Model):
    bank_name = models.CharField(max_length=15, blank=True, null=True)
    card_number = models.CharField(max_length=25, blank=True, null=True)
    number_of_activations = models.IntegerField(blank=True, null=True, default=0)

    def __str__(self):
        return f"Карта банка {self.bank_name}"


class FinishedUser(models.Model):
    GENDER_CHOICES = [
        ('M', 'Мужчина'),
        ('F', 'Женщина'),
    ]

    GOAL_CHOICES = [
        ('G', 'Набрать вес'),
        ('L', 'Сбросить вес'),
    ]

    PLACE_CHOICES = [
        ('H', 'Дом'),
        ('G', 'Зал'),
    ]
    LEVEL = [
        ('P', 'Профессиональный'),
        ('N', 'Новичок'),
    ]

    user = models.IntegerField(primary_key=True)
    username = models.CharField(max_length=100, blank=True, null=True)
    full_name = models.CharField(max_length=100, blank=True, null=True)
    paid_day = models.DateField(blank=True, null=True)
    calories = models.IntegerField(blank=True, null=True)
    timezone = models.CharField(max_length=100)
    пол = models.CharField(max_length=7, choices=GENDER_CHOICES, default='M')
    цель = models.CharField(max_length=12, choices=GOAL_CHOICES, default='G')
    место = models.CharField(max_length=3, choices=PLACE_CHOICES, default='H')
    уровень = models.CharField(max_length=16, choices=LEVEL, default='P')

    def __str__(self):
        return f"{self.username} ({self.user})"

    class Meta:
        app_label = 'telegram_bot'


class SupportTicket(models.Model):
    user_id = models.IntegerField(blank=True, null=True)
    username = models.CharField(max_length=100, blank=True, null=True)
    full_name = models.CharField(max_length=100, blank=True, null=True)
    question = models.CharField(max_length=3000, blank=True, null=True)
    answer = models.CharField(max_length=3000, blank=True, null=True)



