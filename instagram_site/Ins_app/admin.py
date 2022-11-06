from django.contrib import admin
from .models import Insight,Post,HashTag
# Register your models here.

admin.site.register(Insight)
admin.site.register(Post)
admin.site.register(HashTag)