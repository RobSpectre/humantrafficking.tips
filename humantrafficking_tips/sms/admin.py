from django.contrib import admin

from .models import Reporter
from .models import Statement
from .models import Tip
from .models import Photo 


admin.site.register(Reporter)
admin.site.register(Statement)
admin.site.register(Tip)
admin.site.register(Photo)
