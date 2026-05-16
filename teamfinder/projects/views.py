from django.shortcuts import get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.urls import reverse
from .models import Project
from .forms import ProjectForm

class ProjectListView(ListView):
    model = Project
    template_name = 'projects/project_list.html'
    context_object_name = 'projects'
    paginate_by = 12

    def get_queryset(self):
        return Project.objects.filter(status='open').order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context['favorites'] = self.request.user.favorites.values_list('id', flat=True)
        return context

class ProjectDetailView(DetailView):
    model = Project
    template_name = 'projects/project-details.html'
    context_object_name = 'project'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context['is_participant'] = self.object.is_participant(self.request.user)
            context['is_favorite'] = self.object.interested_users.filter(id=self.request.user.id).exists()
        return context

class ProjectCreateView(LoginRequiredMixin, CreateView):
    model = Project
    form_class = ProjectForm
    template_name = 'projects/create-project.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_edit'] = False
        return context

    def form_valid(self, form):
        project = form.save(commit=False)
        project.owner = self.request.user
        project.save()
        project.participants.add(self.request.user)
        return redirect('projects:detail', pk=project.pk)

class ProjectEditView(LoginRequiredMixin, UpdateView):
    model = Project
    form_class = ProjectForm
    template_name = 'projects/create-project.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_edit'] = True
        context['project'] = self.get_object()
        return context

    def dispatch(self, request, *args, **kwargs):
        project = self.get_object()
        if project.owner != request.user and not request.user.is_staff:
            return redirect('projects:detail', pk=project.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('projects:detail', kwargs={'pk': self.object.pk})

@login_required
def complete_project(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if project.owner != request.user and not request.user.is_staff:
        return JsonResponse({'status': 'error', 'message': 'Нет прав'}, status=403)
    if project.status == 'open':
        project.status = 'closed'
        project.save()
        return JsonResponse({'status': 'ok', 'project_status': 'closed'})
    return JsonResponse({'status': 'error', 'message': 'Проект уже завершён'})

@login_required
def toggle_participate(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if project.is_participant(request.user):
        project.participants.remove(request.user)
        is_participant = False
    else:
        project.participants.add(request.user)
        is_participant = True
    return JsonResponse({'status': 'ok', 'is_participant': is_participant})

@login_required
def toggle_favorite(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if project.interested_users.filter(id=request.user.id).exists():
        request.user.favorites.remove(project)
        favorited = False
    else:
        request.user.favorites.add(project)
        favorited = True
    return JsonResponse({'status': 'ok', 'favorited': favorited})

class FavoriteProjectsView(LoginRequiredMixin, ListView):
    template_name = 'projects/favorite_projects.html'
    context_object_name = 'projects'
    paginate_by = 12

    def get_queryset(self):
        return self.request.user.favorites.all().order_by('-created_at')