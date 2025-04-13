# from django.contrib.auth.middleware import AuthenticationMiddleware
# from django.contrib import messages
# from django.shortcuts import redirect

# class BlockedUserMiddleware(AuthenticationMiddleware):
#     def process_request(self, request):
#         user = request.user
#         if user.is_authenticated and user.blocat:
#             messages.error(request, "Contul tău a fost blocat.")
#             return redirect('/proiect/login')  # Redirecționare către pagina de logare
