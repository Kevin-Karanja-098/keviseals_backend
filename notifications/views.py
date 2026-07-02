from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Device
from .serializers import DeviceSerializer


class RegisterDeviceView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        serializer = DeviceSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        token = serializer.validated_data["fcm_token"]

        Device.objects.update_or_create(

            fcm_token=token,

            defaults={

                "user": request.user,

                "platform": serializer.validated_data["platform"],

                "device_name": serializer.validated_data.get(
                    "device_name",
                    "",
                ),

                "is_active": True,
            },
        )

        return Response(
            {"message": "Device registered"},
            status=status.HTTP_200_OK,
        )
    
class RemoveDeviceView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        token = request.data.get("fcm_token")

        Device.objects.filter(

            user=request.user,

            fcm_token=token,

        ).delete()

        return Response(
            {"message": "Device removed"}
        )