from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.tokens import PasswordResetTokenGenerator

from rest_framework import serializers

from apps.account.email import send_email_to_user


User = get_user_model()

class UserSignupSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    password2 = serializers.CharField(max_length=128, style={'input_type': 'password'}, write_only=True)
    class Meta:
        model = User
        fields = [
            'email', 'first_name', 'last_name', 'password', 'password2',
        ]
        extra_kwargs = {
            'password': {'write_only': True},
        }
        
    def validate(self, attrs):
        first_name = attrs.get('first_name')
        last_name = attrs.get('last_name')
        password = attrs.get('password')
        password2 = attrs.get('password2')
        if not first_name:
            raise serializers.ValidationError(
                "Le prénom ne doit pas être null"
            )
        if not last_name:
            raise serializers.ValidationError(
                "Le nom ne doit pas être null"
            )
        if password and password2 and password != password2:
            raise serializers.ValidationError(
                "Le mot de passe et le mot de passe de confirmation ne correspondent pas."
            )
        return attrs
    
    def create(self, validate_data):
        validate_data.pop('password2', None)
        return User.objects.create_user(**validate_data)

class UserLoginSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(max_length=255)
    class Meta:
        model = User
        fields = [
            'email', 'password',
        ]

class UserProfilSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name',
        ]


class UserChangePasswordSerializer(serializers.Serializer):
    password = serializers.CharField(max_length=128, style={'input_type': 'password'}, write_only=True)
    password2 = serializers.CharField(max_length=128, style={'input_type': 'password'}, write_only=True)
    class Meta:
        fields = ['password', 'password2']

    def validate(self, attrs):
        password = attrs.get('password')
        password2 = attrs.get('password2')
        user = self.context.get('user')
        if password != password2:
            raise serializers.ValidationError(
                "Le mot de passe et le mot de passe de confirmation ne correspondent pas."
            )
        user.set_password(password)
        user.save()
        return attrs

class SendEmailResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=255)
    class Meta:
        fields = ['email']
        
    def validate(self, attrs):
        email = attrs.get('email')
        current_site = self.context.get('current_site')
        if User.objects.filter(email=email).exists():
            user = User.objects.get(email=email)
            token = PasswordResetTokenGenerator().make_token(user)
            send_email_to_user(
                subject=f"Réinitialisation du mot de passe sur {current_site}",
                template_name='account/send_email_reset_password.html',
                user=user,
                token=token,
                domain=settings.DOMAIN_FRONTEND
            )
        else:
            raise serializers.ValidationError(
                "L'adresse email n'exist pas !"
            )
        return attrs

class UserResetPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(max_length=128, style={'input_type': 'password'}, write_only=True)
    password2 = serializers.CharField(max_length=128, style={'input_type': 'password'}, write_only=True)
    class Meta:
        fields = ['password', 'password2']
        
    def validate(self, attrs):
        password = attrs.get('password')
        password2 = attrs.get('password2')
        uid = self.context.get('uid')
        token = self.context.get('token')
        if password != password2:
            raise serializers.ValidationError(
                "Le mot de passe et le mot de passe de confirmation ne correspondent pas."
            )
        try:
            uid = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=uid)
        except Exception as e:
            user = None
        if user and PasswordResetTokenGenerator().check_token(user, token):
            user.set_password(password)
            user.save()
            send_email_to_user(
                subject=f"{settings.DOMAIN_FRONTEND} - Votre mot de passe a été modifié avec succès !", 
                template_name='account/password_rest_success.html', 
                user=user, 
                domain=settings.DOMAIN_FRONTEND
            )
        else:
            raise serializers.ValidationError(
                "Votre demande de réinitialisation du mot de passe est expirer"
            )
        return attrs