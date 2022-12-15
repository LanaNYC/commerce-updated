"""
items for 'auction' are from
https://harrypotter.fandom.com/wiki/
"""

from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.db.models import Max, Value
from django.db.models import query
from django.db.models.query import EmptyQuerySet, QuerySet
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django import forms
from django.forms import ModelForm

from .models import User, Category, Listing, Bid, Comment, Watchlist
from auctions import models


# Create the form class.
class newListingForm(ModelForm):
    class Meta:
        model = Listing
        fields = ['title', 'description', 'starting_bid', 'image', 'category', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs=
                {'class': "form-control"} ),
            'description': forms.Textarea(attrs=
                {'class': "form-control", 'rows': 4}),  
            'starting_bid': forms. NumberInput(attrs=
                {'class': "form-control"}),
            'image': forms.URLInput(attrs=
                {'class': "form-control"}),
            'category': forms.Select(attrs=
                {'class': "form-control"}),
            
        }
  

class bidForm(ModelForm):
    class Meta:
        model = Bid
        fields = ['ammount'] 

class newCommentForm(ModelForm):
    class Meta:
        model = Comment
        fields  = ['commentText']             
        


def index(request):
    """
    Display All active listings for ALL users (loggedin or not)
    """
    listings = Listing.objects.filter(is_active = True).order_by("title")
    return render(request, "auctions/index.html", {
        "listings": listings
    })

    
def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")


@login_required
def my_listing(request, user_id):
    """
    Display All active listings for one logged in user only.
    """

    current_user = User.objects.get(pk=user_id)
    filtered_listings = Listing.objects.filter(user_id=user_id, is_active = True)
    return render(request, "auctions/index.html", {
       "listings": filtered_listings
    })


def listing(request, listing_id):
    """
    Display Individual Listing Page.
    """
    if request.user.is_authenticated: 
        listing = Listing.objects.get(pk=listing_id)  
        item = Watchlist.objects.filter(listing=listing_id, user=request.user)
        current_price = calculate_current_price(listing_id)
        owner = find_owner(listing_id)
        current_user = request.user.id
        active = listing.is_active == True
       
        have_bid_QS = Bid.objects.filter(listing=listing)
        if not have_bid_QS:
            winner_id = None
        else:
            winner = get_winner(listing)
            winner_id = winner.user.id
       
        comments = Comment.objects.filter(listing = listing)
        if not comments:    
            comments = None
        return render(request, "auctions/listing.html", {
            "listing": listing,
            "item": item,
            "current_price": current_price,
            "owner":owner ,
            "current_user": current_user,
            "active": active,
            "winner_id": winner_id,
            "comments": comments,
        })
    else:
        return render(request, "auctions/login.html", {
                "message": "Please log in to continue."
            })


@login_required
def closed_listing(request, user_id):
    current_user = User.objects.get(pk=user_id)
    closed_listings = Listing.objects.filter(is_active = False, user_id=user_id)
    if closed_listings: 
        return render(request, "auctions/closed_listings.html", {
        "closed_listings": closed_listings,
        "user": current_user
        })
    else:
        return render(request, "auctions/closed_listings.html", {
        "message": "You don't have any closed auctions yet.",
        "user": current_user
        })


@login_required
def add_watchlist(request, listing_id):
    """
    Add a listing to a Watchlist
    """
    if request.method == "POST":
        listing = Listing.objects.get(pk=listing_id)
        if request.user.is_authenticated:
            user = request.user 
            new_watched_listing = Watchlist()
            new_watched_listing.user = request.user
            new_watched_listing.listing = listing
            new_watched_listing.save()
            return render(request, "auctions/listing.html", {
            "listing": listing,
            "message": "This auction was added to your watchlist."
            })
        else:
            return render(request, "auctions/login.html", {
                "message": "Please log in."
            })


@login_required
def remove_watchlist(request, listing_id):
    """
    Remove a listing to a Watchlist
    """
    if request.method == "POST":
        listing = Listing.objects.get(pk=listing_id)
        if request.user.is_authenticated:
            user = request.user 
            watched_listing = Watchlist.objects.filter(listing=listing_id, user=request.user)
            watched_listing.delete()
            return render(request, "auctions/listing.html", {
            "listing": listing,
            "message": "This auction was removed from your watchlist."
            })
        else:
            return render(request, "auctions/login.html", {
                "message": "Please log in."
            })
   

@login_required
def watchlist(request, user_id):
    """
    Display all of the listings that a user has added to their watchlist. 
    """
    current_user = User.objects.get(pk=user_id)
    filtered_watchlist = Watchlist.objects.filter(user_id=user_id)
    if filtered_watchlist:    
        return render(request, "auctions/watchlist.html", {
        "watchlist": filtered_watchlist,
        "user": current_user
        })
    else:
        return render(request, "auctions/watchlist.html", {
        "message": "You don't watch any auctions yet.",
        "user": current_user
        })


@login_required
def create_listing(request, user_id):

    if request.method == "POST":
        form = newListingForm(request.POST)
        user = request.user
        if form.is_valid():
            title = request.POST["title"]
            db_title = Listing.objects.filter(title=title, user_id=request.user.id)

            if db_title:
                return render(request, "auctions/create.html", {
                    "form": form,
                    "message": "You already have an auction with this title."
                })  
            else:   
                new_auction=form.save(commit=False)
                new_auction.user_id= user
                new_auction.save()
                return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/create.html", {
                "form": newListingForm(),
                "message": "Your form is invalid."
            })   
    # If the method is GET, User will see an empty form
    else:
        return render(request, "auctions/create.html", {
            "form": newListingForm()
        })


@login_required
def place_bid(request, listing_id):
   
    if request.method == "POST":
        form = bidForm(request.POST)
        listing = Listing.objects.get(pk=listing_id)
        user_id = request.user.id
        has_abid = Bid.objects.filter(listing=listing)
        user = request.user
       
        if not has_abid:   
            query_dic = Listing.objects.filter(pk=listing_id).values("starting_bid")
            for q in query_dic:
                current_price = q["starting_bid"]               
            new_bid = int(request.POST["ammount"])    
            
            if new_bid > current_price:
                save_bid_to_DB(new_bid, user, listing)
                return render(request, "auctions/listing.html", {
                "listing": listing,
                "listing.id": listing.id,
                "current_price": new_bid,
                "message": "You palced your bid."
                })  
            else:
                return render(request, "auctions/listing.html", {
                "form": form,
                "listing": listing,
                "listing.id": listing.id,
                "current_price": current_price,
                "message": "Your bid must be greater current price."
            })
        else:
            #Have at least one bidding
            current_price = calculate_current_price(listing_id)
            new_bid = int(request.POST["ammount"])
            if new_bid > current_price:
                save_bid_to_DB(new_bid, user, listing)
                return render(request, "auctions/listing.html", {
                "listing": listing,
                "listing.id": listing.id,
                "has_abid": has_abid,
                "current_price": new_bid,
                "message": "You palced your bid."
                })
            else:
                return render(request, "auctions/listing.html", {
                "listing": listing,
                "listing.id": listing.id,
                "current_price": current_price,
                "message": "Your bid must be greater current price."
                })  
    # If the method is GET, User will see an empty form
    else:
        return render(request, "auctions/listing.html", {
            "form": bidForm()
        })
    

def calculate_current_price(listing_id):
    listing = Listing.objects.get(pk=listing_id)
    max_query_dic = Bid.objects.filter(listing=listing).aggregate(Max('ammount'))
    current_price = max_query_dic["ammount__max"]
    return(current_price)


def save_bid_to_DB(new_bid, user, listing):
    new_bid_form = Bid()
    new_bid_form.ammount = new_bid
    new_bid_form.user = user
    new_bid_form.listing = listing
    new_bid_form.winning = False
    new_bid_form.save()


@login_required
def close_listing(request, listing_id):
    if request.method == "POST":
        if request.user.is_authenticated:   
            current_user = request.user.id
            owner = find_owner(listing_id)
            if current_user == owner:
                listing = Listing.objects.get(pk=listing_id)
                listing.is_active = False
                listing.save()
                winner = get_winner(listing)
                winner.winning = True
                winner.save()
                return HttpResponseRedirect(reverse("index"))

                
def find_owner(listing_id):
    query_owner = Listing.objects.filter(pk=listing_id).values("user_id")
    for q in query_owner:
        owner = q["user_id"]  
    return(owner)               


def get_winner(listing):   
    max_query_dic = Bid.objects.filter(listing=listing).aggregate(Max('ammount'))
    winning_bid = max_query_dic["ammount__max"]
    winner_id_QS = Bid.objects.filter(listing=listing, ammount = winning_bid).values("user")
    for q in winner_id_QS:
        winner_id = q["user"]  

    winner_QS = Bid.objects.filter(listing=listing, ammount = winning_bid, user = winner_id)
    for winner in winner_QS:
        return(winner)


@login_required
def add_comment(request, listing_id):
    """
    Users who are signed in should be able to add comments to the listing page. 
    """
    user = request.user
    listing = Listing.objects.get(pk = listing_id)
    listing = listing
    if request.method == "POST":
        form = newCommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = user
            comment.listing = listing
            comment.commentText = request.POST["comment"]
            comment.save()
            return HttpResponseRedirect(reverse("listing", args=[listing_id])) 
        else:
            return render(request, "auctions/listing.html", {
             "form": newCommentForm(),
                "message": "Your form is invalid."
            })   
    # If the method is GET, User will see an empty form
    else:
        return render(request, "auctions/listing.html", {
                "form": newCommentForm(),
                })   


def all_categories(request):
        
    categories = Category.objects.order_by("description")
    return render(request, "auctions/all_categories.html", {
        "categories": categories
    })
    

def display_category(request, category_id):
     
    listings = Listing.objects.filter(is_active = True, category_id=category_id).order_by("title")
    return render(request, "auctions/index.html", {
        "listings": listings
    })
    
