from django.shortcuts import render

# Example view function
def home(request):
    return render(request, 'home.html')
