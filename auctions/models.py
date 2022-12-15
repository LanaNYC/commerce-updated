from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    id = models.AutoField(primary_key=True)

    def __str__(self):
        return f"{self.username}"

class Category(models.Model):
    id = models.AutoField(primary_key=True)
    description = models.CharField(max_length=150)
    
    def __str__(self):
        return f" {self.description}"

class Listing(models.Model):
    id = models.AutoField(primary_key=True)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name="listings") 
    title = models.CharField(max_length=64)
    description = models.TextField(blank = True)
    starting_bid = models.PositiveIntegerField() 
    image = models.URLField(blank = True)
    category = models.ForeignKey(Category, null = True, blank=True, on_delete=models.CASCADE, related_name="categories")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.id}: {self.title} created by {self.user_id}"

class Bid(models.Model):
    id = models.AutoField(primary_key=True)
    ammount = models.PositiveIntegerField()
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="userBids") 
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="allListingBids") 
    winning = models.BooleanField(default=False)

    def __str__(self):
                return f"{self.ammount} by {self.user} to {self.listing}"

class Watchlist(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name="watchedListings")
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE) #May need to add related_name

    def __str__(self):
        return f"{self.user} is watching {self.listing}"

class Comment(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True, related_name="comments")  
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, blank=True, null=True, related_name="allListingComments") 
    commentText = models.TextField(blank = True)

    def __str__(self):
        return f"{self.commentText} by {self.user}"   







