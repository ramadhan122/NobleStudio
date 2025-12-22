from django.db import models

class Photographer(models.Model):
    name = models.CharField(max_length=100)
    bio = models.TextField()
    profile_image = models.ImageField(upload_to='media/photographers/')
    contact_email = models.EmailField()
    phone = models.CharField(max_length=20)
    instagram = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)

class Category(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

class Work(models.Model):
    photographer = models.ForeignKey(Photographer, on_delete=models.CASCADE, related_name='works')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='works')
    title = models.CharField(max_length=100)
    image_url = models.ImageField(upload_to='media/photos/')
    description = models.TextField()
    shoot_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.title} by {self.photographer.name}"
    
    class Meta:
        ordering = ['-created_at']


class Testimonial(models.Model):
    name = models.CharField(max_length=100)
    role = models.CharField(max_length=100)
    photo = models.ImageField(upload_to='testimonials/')
    message = models.TextField()
    rating = models.PositiveSmallIntegerField(default=5)
    created_at = models.DateTimeField(auto_now_add=True)
    approved = models.BooleanField(default=False)  # << tambahkan agar bisa diset oleh admin nanti


