from rest_framework.permissions import BasePermission

from accounts.models import LandlordContract, LandlordProfile


class IsLandlord(BasePermission):

    def has_permission(
        self,
        request,
        view
    ):

        return (
            request.user.is_authenticated
            and request.user.role == "LANDLORD"
        )
    
class IsTenant(BasePermission):

    def has_permission(
        self,
        request,
        view
    ):

        return (
            request.user.is_authenticated
            and request.user.role == "TENANT"
        )
    
class IsPropertyManager(BasePermission):

    def has_permission(
        self,
        request,
        view
    ):

        return (
            request.user.is_authenticated
            and request.user.role == "PROPERTY_MANAGER"
        )
    
class IsActiveLandlord(BasePermission):

    def has_permission(self, request, view):

        if request.user.role != "LANDLORD":
            return False

        profile = LandlordProfile.objects.filter(
            user=request.user
        ).first()

        if not profile:
            return False

        contract = LandlordContract.objects.filter(
            landlord=profile
        ).first()

        return (
            profile.status == "ACTIVE"
            and
            contract
            and
            contract.status == "APPROVED"
        )