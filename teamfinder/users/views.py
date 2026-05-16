from django.shortcuts import redirect
from django.views.generic import ListView, DetailView, UpdateView, CreateView, FormView
from django.contrib.auth import get_user_model, login, authenticate, logout, update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.contrib.auth.forms import PasswordChangeForm
from .forms import RegistrationForm, LoginForm, UserEditForm

User = get_user_model()

class UserListView(ListView):
    model = User
    template_name = 'users/participants.html'
    context_object_name = 'participants'
    paginate_by = 12

    def get_queryset(self):
        return User.objects.filter(is_active=True).order_by('id')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        filter_type = self.request.GET.get('filter')
        
        if self.request.user.is_authenticated and filter_type:
            user = self.request.user
            
            if filter_type == 'favorite_authors':
                favorite_projects = user.favorites.all()
                context['participants'] = User.objects.filter(
                    owned_projects__in=favorite_projects
                ).distinct().order_by('id')
                context['active_filter'] = filter_type
                
            elif filter_type == 'my_participated_projects_authors':
                participated_projects = user.participated_projects.all()
                context['participants'] = User.objects.filter(
                    owned_projects__in=participated_projects
                ).exclude(id=user.id).distinct().order_by('id')
                context['active_filter'] = filter_type
                
            elif filter_type == 'users_who_like_my_projects':
                my_projects = user.owned_projects.all()
                context['participants'] = User.objects.filter(
                    favorites__in=my_projects
                ).exclude(id=user.id).distinct().order_by('id')
                context['active_filter'] = filter_type
                
            elif filter_type == 'my_project_participants':
                my_projects = user.owned_projects.all()
                context['participants'] = User.objects.filter(
                    participated_projects__in=my_projects
                ).exclude(id=user.id).distinct().order_by('id')
                context['active_filter'] = filter_type
        
        return context

class UserDetailView(DetailView):
    model = User
    template_name = 'users/user-details.html'
    context_object_name = 'user_obj'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['projects'] = self.object.owned_projects.filter(status='open').order_by('-created_at')
        return context

class RegisterView(CreateView):
    template_name = 'users/register.html'
    form_class = RegistrationForm

    def form_valid(self, form):
        user = form.save(commit=False)
        user.set_password(form.cleaned_data['password'])
        user.phone = '+70000000000'
        user.save()
        login(self.request, user)
        return redirect('projects:list')

    def form_invalid(self, form):
        return self.render_to_response({'form': form})

class LoginView(FormView):
    template_name = 'users/login.html'
    form_class = LoginForm

    def form_valid(self, form):
        email = form.cleaned_data['email']
        password = form.cleaned_data['password']
        user = authenticate(self.request, email=email, password=password)
        if user is not None:
            login(self.request, user)
            return redirect('projects:list')
        form.add_error(None, 'Неверный имейл или пароль')
        return self.form_invalid(form)

def logout_view(request):
    logout(request)
    return redirect('projects:list')

class UserEditView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserEditForm
    template_name = 'users/edit_profile.html'

    def get_object(self):
        return self.request.user

    def get_success_url(self):
        return reverse('users:detail', kwargs={'pk': self.request.user.pk})

class ChangePasswordView(LoginRequiredMixin, FormView):
    template_name = 'users/change_password.html'
    form_class = PasswordChangeForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.save()
        update_session_auth_hash(self.request, form.user)
        return redirect('users:detail', pk=self.request.user.pk)