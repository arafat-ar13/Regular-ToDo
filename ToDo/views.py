from django.shortcuts import render, redirect, HttpResponseRedirect
from django.contrib import messages
from .models import ToDo, SubTask
from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse, reverse_lazy
from users.models import Profile
from django.contrib.auth.models import User
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import NewTaskForm, DueDateForm, SubTaskForm

import datetime


def home(request):
    if request.method == "POST":
        due_form = DueDateForm(request.POST)
        add_form = NewTaskForm(request.POST)

        if due_form.is_valid():
            days = due_form.cleaned_data.get("due_date").lower()

            if days == "today":
                days = 0
            elif days == "tomorrow":
                days = 1
            elif days == "next week":
                days = 7
            elif days == "yesterday":
                days = -1
            elif days == "last week":
                days = -7
            else:
                days = int(days)

            today = datetime.datetime.today()
            due_date = today + datetime.timedelta(days=days)


            todo = ToDo.objects.get(pk=int(request.POST.get("title", "")))
            todo.due_date = due_date
            todo.save()

            messages.success(request, "Due Date added to task")

            return redirect("todo-home")


        elif add_form.is_valid():
            title = add_form.cleaned_data.get("title")
            todo = ToDo(title=title)
            todo.creator = request.user
            todo.save()

            user = User.objects.get(username=request.user.username)
            user.profile.todos += 1
            user.profile.total_todos += 1
            user.save()
            messages.success(request, "Your new task has been added")

            return redirect("todo-home")

    else:
        add_form = NewTaskForm()
        due_form = DueDateForm()

    todos = ToDo.objects.all()

    # Handling how the user's tasks should be sorted
    if request.user.is_authenticated:
        user = User.objects.get(username=request.user.username)

        if user.profile.sort_todos_by == "date_added":
            sorter = "date_posted"
            todos = ToDo.objects.all().order_by(sorter).reverse()
        elif user.profile.sort_todos_by == "due_date":
            sorter = "due_date"

            due_todos = []
            normal_todos = []

            for todo in ToDo.objects.all().order_by("due_date"):
                if todo.due_date is not None:
                    due_todos.append(todo)

            for todo in ToDo.objects.all():
                if todo.due_date is None:
                    normal_todos.append(todo)

            normal_todos.reverse()
            todos = due_todos + normal_todos


    # Checking today's date and comparing colors of due dates
    today = datetime.datetime.today()
    todo_objects = ToDo.objects.all()

    for todo in todo_objects:
        if todo.due_date is not None:
            if todo.due_date.day > today.day:
                todo.due_date_color = "green"
            elif todo.due_date.day == today.day:
                todo.due_date_color = "blue"
            elif todo.due_date.day < today.day:
                todo.due_date_color = "red"

            todo.save()     


    context = {
        "todos": todos,
        "add_form": add_form,
        "due_form": due_form
    }

    return render(request, "ToDo/home.html", context=context)


def remove_due_date(request, pk):
    todo = ToDo.objects.get(pk=pk)
    todo.due_date = None
    todo.due_date_color = None

    todo.save()
    messages.info(request, "Due Date removed")

    return redirect("todo-home")


def about(request):
    return render(request, "ToDo/about.html")


def toggle_user_sort(request):
    user = User.objects.get(username=request.user.username)
    if user.profile.sort_todos_by == "date_added":
        user.profile.sort_todos_by = "due_date"
    else:
        user.profile.sort_todos_by = "date_added"

    user.save()

    messages.success(request, "Your sort order altered")

    return redirect("todo-home")


def toggle_dark_mode(request):
    user = User.objects.get(username=request.user.username)

    if user.profile.has_dark_mode:
        user.profile.has_dark_mode = False
        message = "Dark Mode disabled"
    else:
        user.profile.has_dark_mode = True
        message = "Welcome to the Dark Side"

    user.save()

    messages.success(request, message)

    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))


def delete(request, pk):
    todo = ToDo.objects.get(pk=pk)

    if not todo.is_checked:
        user = User.objects.get(username=request.user.username)
        user.profile.todos -= 1
        user.profile.total_todos -= 1
        user.save()

    todo.delete()
    messages.info(request, "Item removed!!")

    return redirect('todo-home')


def check_todo(request, pk):
    todo = ToDo.objects.get(pk=pk)
    todo.is_checked = True
    todo.save()
    messages.success(request, "Sweeet! Congrats!!")

    user = User.objects.get(username=request.user.username)
    user.profile.todos -= 1
    user.save()

    return redirect("todo-home")

def uncheck_todo(request, pk):
    todo = ToDo.objects.get(pk=pk)
    todo.is_checked = False
    todo.save()

    user = User.objects.get(username=request.user.username)
    user.profile.todos += 1
    user.save()

    return redirect("todo-home")


def add_subtask(request, pk):
    todo = ToDo.objects.get(pk=pk)
    subtasks = SubTask.objects.filter(parent_task=todo.title)

    if request.method == "POST":
        subtask_form = SubTaskForm(request.POST)

        if subtask_form.is_valid():
            subtask_title = subtask_form.cleaned_data.get("sub_task")

            subtask = SubTask(title=subtask_title)
            subtask.parent_task = todo.title
            subtask.identification_id = todo.pk

            todo.num_of_subtasks += 1
            todo.save()

            subtask.save()

            messages.success(request, "Subtask added")

            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
    
    else:
        subtask_form = SubTaskForm()


    context = {
        "todo": todo,
        "subtask_form": subtask_form,
        "subtasks": subtasks
    }

    return render(request, "ToDo/subtasks.html", context=context)


def delete_subtask(request, pk):
    subtask = SubTask.objects.get(pk=int(pk))

    parent_todo = ToDo.objects.get(pk=subtask.identification_id)
    parent_todo.num_of_subtasks -= 1
    parent_todo.save()

    subtask.delete()

    messages.info(request, "Item removed!!")

    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))


def toggle_subtask(request, pk):
    subtask = SubTask.objects.get(pk=int(pk))

    if subtask.done:
        subtask.done = False
        subtask.save()

        messages.info(request, "Okay, take your time!")

    else:

        subtask.done = True
        subtask.save()

        messages.info(request, "Awesome!")

    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))


class TodoCompletedView(ListView):
    model = ToDo
    template_name = "ToDo/completed.html"
    context_object_name = "todos"
    ordering = ["-date_posted"]


class TodoUpdateView(LoginRequiredMixin, UpdateView):
    model = ToDo
    fields = ["title"]
    success_url = reverse_lazy("todo-home")

    def form_valid(self, form):
        form.instance.creator = self.request.user
        messages.info(self.request, "Your task has been edited")
        return super().form_valid(form)


class SubtaskUpdateView(LoginRequiredMixin, UpdateView):
    model = SubTask
    fields = ["title"]
    success_url = reverse_lazy("todo-add-subtask")

    def form_valid(self, form):
        form.instance.creator = self.request.user
        messages.info(self.request, "Your subtask has been edited")


        return super().form_valid(form)
