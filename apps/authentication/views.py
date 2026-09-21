from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from .forms import RegisterForm


def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('core:dashboard')
    else:
        form = RegisterForm()
    return render(request, 'authentication/register.html', {'form': form})


class CustomLoginView(LoginView):
    template_name = 'authentication/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy('core:dashboard')


def logout_view(request):
    """
    GET: show a confirmation page with a closing dua ("kaffarat al-majlis")
    and a confirm button — the session is NOT ended yet at this point.
    POST: the user actually confirmed, so now we end the session for real.
    """
    if request.method == 'POST':
        logout(request)
        return redirect('authentication:login')
    return render(request, 'authentication/logout_confirm.html')
