
from blog.models import Category, Post
from django.core.management.base import BaseCommand






class Command(BaseCommand):
    help = 'This commands inserts Category data'

   


    def handle(self, *args, **options):

         #delete existing data
        Category.objects.all().delete()

        categories = ['sports','Technology','science','Arts','Food']


        for category_name in categories:
            Category.objects.create(name= category_name)

        self.stdout.write(self.style.SUCCESS('Completed inserting Data'))
        