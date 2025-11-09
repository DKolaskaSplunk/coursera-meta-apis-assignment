from django.contrib.auth.models import User


def is_customer(user: User) -> bool:
    if user.groups.filter(name="Manager").exists():
        return False
    if user.groups.filter(name="Delivery Crew").exists():
        return False
    return True


def is_manager(user: User) -> bool:
    return user.groups.filter(name="Manager").exists()


def is_delivery_crew(user: User) -> bool:
    return user.groups.filter(name="Delivery Crew").exists()
