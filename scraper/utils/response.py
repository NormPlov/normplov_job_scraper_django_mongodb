from datetime import datetime
from rest_framework.response import Response

def BaseResponse(status: int, message: str, payload=None):

    return Response({
        "date": datetime.now().isoformat(),
        "status": status,
        "message": message,
        "payload": payload
    }, status=status)
