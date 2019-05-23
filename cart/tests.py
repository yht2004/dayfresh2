from django.test import TestCase
from django.shortcuts import render
from django.views.generic import View
from django.http import JsonResponse
from django_redis import get_redis_connection
from django.contrib.auth.mixins import LoginRequiredMixin

from good.models import GoodsSKU


# Create your tests here.
