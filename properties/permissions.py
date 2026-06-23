from rest_framework.permissions import BasePermission

from accounts.models import (
    LandlordProfile,
    LandlordContract
)


class IsActiveLandlord(BasePermission):

    def has_permission(
        self,
        request,
        view
    ):

        if not request.user.is_authenticated:
            return False

        if request.user.role != "LANDLORD":
            return False

        profile = (
            LandlordProfile.objects.filter(
                user=request.user
            ).first()
        )

        if not profile:
            return False

        contract = (
            LandlordContract.objects.filter(
                landlord=profile
            ).first()
        )

        return (
            profile.status == "ACTIVE"
            and contract
            and contract.status == "APPROVED"
        )