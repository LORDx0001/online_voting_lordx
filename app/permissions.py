from rest_framework.permissions import BasePermission

class IsStaff(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == 3
        )
    
# IsStaff permission klassi:
# - Django REST Framework uchun maxsus ruxsat (permission) klassi.
# - Faqat staff (role == 3) bo‘lgan foydalanuvchilarga ruxsat beradi.
# - has_permission() metodi:
#     - Foydalanuvchi login bo‘lganini (is_authenticated) tekshiradi.
#     - Foydalanuvchi roli 3 (staff) ekanini tekshiradi.
# - Agar shartlar bajarilsa, endpointga ruxsat beradi, aks holda rad etadi.