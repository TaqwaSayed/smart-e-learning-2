"""
App-level permission layer for course/lesson management.

This is the piece that makes the INSTRUCTOR / STUDENT split visible and
*enforced* in the student-facing app (not just in /admin/, see
apps/learning/admin.py for the equivalent admin-side guard).

Two independent checks are combined everywhere below:
1. Role check   — the account must be an INSTRUCTOR (or ADMIN/superuser).
2. Ownership     — an instructor may only manage the courses/lessons they
                    themselves teach, never another instructor's course.

Both checks are enforced *server-side*, on every view, regardless of what
the template shows or hides. Hiding an "Edit" button from a student is a
UX nicety, not a security control — the real control is here. A student
(or another instructor) who guesses/bookmarks an edit URL still gets a
403, not the form.
"""
from django.core.exceptions import PermissionDenied
from functools import wraps


def can_manage_courses(user) -> bool:
    """Can this account create course content at all (role-level check)?"""
    return user.is_authenticated and (
        user.is_superuser or getattr(user, 'role', None) in ('INSTRUCTOR', 'ADMIN')
    )


def can_manage_course(user, course) -> bool:
    """Can this specific account manage this specific course (role + ownership)?"""
    if not can_manage_courses(user):
        return False
    if user.is_superuser or getattr(user, 'role', None) == 'ADMIN':
        return True
    return course.instructor_id == user.id


def instructor_required(view_func):
    """
    Blocks the view entirely for anyone who isn't at least an instructor.
    Use for "create" views, where there's no existing object to check
    ownership against yet.
    """
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        if not can_manage_courses(request.user):
            raise PermissionDenied("Only instructors can manage course content.")
        return view_func(request, *args, **kwargs)
    return wrapped
