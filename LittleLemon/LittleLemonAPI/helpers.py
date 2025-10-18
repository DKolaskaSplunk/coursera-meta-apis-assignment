from django.contrib.auth.models import User


def is_customer(user: User) -> bool:
    if user.groups.filter(name="Manager").exists():
        return False
    if user.groups.filter(name="Delivery Crew").exists():
        return False
    return True
