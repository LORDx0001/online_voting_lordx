# Bu faylda barcha asosiy API endpointlar va yordamchi funksiyalar joylashgan.
# Funksiya-based viewlar ishlatilgan (har bir endpoint uchun alohida funksiya).
# @api_view dekoratori yordamida endpointlar HTTP metodlari bilan belgilanadi.
# @swagger_auto_schema yordamida Swagger uchun avtomatik hujjatlash qo‘shiladi.
# Har bir endpoint uchun serializerlar orqali ma’lumotlar validatsiya qilinadi.

# Nima uchun aynan shu usul tanlangan va qanday yechimlar beradi:
# 1. Funksiya-based viewlar (FBV) — har bir endpoint mustaqil, kod oson o‘qiladi va test qilinadi.
# 2. Serializerlar — kiruvchi ma’lumotlarni tekshiradi, xatoliklarni aniq ko‘rsatadi, xavfsizlikni oshiradi.
# 3. JWT tokenlar va OTP — autentifikatsiya va telefon raqamini tasdiqlash uchun ishlatiladi, xavfsizlikni ta’minlaydi.
# 4. Permission klasslari — rollar bo‘yicha (masalan, staff) endpointlarga kirishni boshqaradi.
# 5. Swagger dekoratorlari — frontend va test uchun avtomatik API hujjatlash beradi.
# 6. Har bir funksiya qisqa va aniq, DRF standartlariga mos, kengaytirish va debugging oson.

# home() - Bosh sahifa uchun HTML render qiladi.
# send_otp_to_telegram() - OTP kodini Telegram bot orqali yuboradi.

# register() - Foydalanuvchini ro‘yxatdan o‘tkazadi, telefon raqamini tekshiradi, OTP yuboradi.
# verify_otp() - Telefon raqamini OTP orqali tasdiqlaydi.
# login_view() - Foydalanuvchini login qiladi, JWT token qaytaradi.
# resend_otp() - Telefon raqami tasdiqlanmagan bo‘lsa, yangi OTP yuboradi.

# poll_list() - Barcha poll (so‘rovnoma)larni va ularning nomzodlarini ko‘rsatadi.
# poll_detail() - Bitta poll va unga tegishli nomzodlar va ovozlar sonini ko‘rsatadi.

# vote() - Foydalanuvchi ovoz beradi. Har bir poll uchun faqat bir marta ovoz berish mumkin.
# my_votes() - Foydalanuvchining barcha ovozlarini ko‘rsatadi.

# create_poll() - Staff foydalanuvchi yangi poll yaratishi mumkin (IsStaff permission).
# create_candidate() - Staff foydalanuvchi yangi kandidat yaratishi mumkin (IsStaff permission).

# reset_password() - Foydalanuvchi eski va yangi parol bilan parolni o‘zgartiradi.
# forgot_password() - Parolni unutgan foydalanuvchi uchun OTP yuboradi.
# forgot_password_confirm() - OTP va yangi parol orqali parolni tiklaydi.

# user_info() - Foydalanuvchi o‘z ma’lumotlarini ko‘radi.
# update_user_info() - Foydalanuvchi o‘z ma’lumotlarini o‘zgartiradi.
# delete_user() - Foydalanuvchi o‘z akkauntini o‘chiradi.

# Har bir endpointda:
# - Ma’lumotlar validatsiyasi va xatoliklar uchun aniq javoblar qaytariladi.
# - Token orqali autentifikatsiya va permissionlar ishlatiladi.
# - Kod qisqa, aniq va DRF standartlariga mos yozilgan.

import re
import random
import requests
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.contrib.auth import authenticate
from .models import Voter, Poll, Candidate, Vote
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from .serializers import (
    RegisterSerializer, VerifyOtpSerializer, LoginSerializer, VoteSerializer,
    PollCreateSerializer, CandidateCreateSerializer, ResetPasswordSerializer,
    ForgotPasswordSendOtpSerializer, ForgotPasswordConfirmSerializer
)
from .permissions import IsStaff
from django.shortcuts import render
from django.utils import timezone
from .serializers import RegisterSerializer
from .serializers import UserUpdateSerializer

def home(request):
    return render(request, 'home.html')

def send_otp_to_telegram(phone, otp):
    token = settings.TELEGRAM_BOT_TOKEN
    chat_id = settings.TELEGRAM_CHAT_ID
    message = f"Телефон номер: {phone}\nOTP код: {otp}"
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {"chat_id": chat_id, "text": message}
    requests.post(url, data=data)

@swagger_auto_schema(method='post', request_body=RegisterSerializer)
@api_view(['POST'])
def register(request):
    first_name = request.data.get('first_name')
    last_name = request.data.get('last_name')
    phone = request.data.get('phone')
    password = request.data.get('password')
    role = int(request.data.get('role', 2))  # 2-voter, 3-staff
    phone_pattern = r'^\+998\d{9}$'
    if not all([first_name, last_name, phone, password]):
        return Response({'error': 'Заполните все поля'}, status=400)
    if not re.match(phone_pattern, phone):
        return Response({'error': 'Телефон номер должен начинаться с +998 и состоять из 13 символов. Например: +998901234567'}, status=400)

    # Если номер уже есть, но не верифицирован - отправить новый OTP
    existing_voter = Voter.objects.filter(phone=phone).first()
    if existing_voter:
        if not existing_voter.is_phone_verified:
            otp = str(random.randint(100000, 999999))
            existing_voter.otp_code = otp
            existing_voter.set_password(password)  # обновить пароль (по желанию)
            existing_voter.save()
            send_otp_to_telegram(phone, otp)
            return Response({'msg': 'Телефон номер еще не подтвержден. Новый OTP код отправлен.'}, status=200)
        else:
            return Response({'error': 'Этот телефон номер уже зарегистрирован'}, status=400)

    # Создание staff или voter по роли
    if role == 3:
        voter = Voter.objects.create_user(
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            password=password,
            role=role,
            is_staff=True,
            is_superuser=False,
        )
    else:
        voter = Voter.objects.create_user(
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            password=password,
            role=role,
            is_staff=False,
            is_superuser=False,
        )
    voter.is_phone_verified = False
    voter.otp_code = str(random.randint(100000, 999999))
    voter.save()
    send_otp_to_telegram(phone, voter.otp_code)
    return Response({'msg': 'Вы успешно зарегистрировались. OTP код отправлен в Telegram.'}, status=201)

@swagger_auto_schema(method='post', request_body=VerifyOtpSerializer)
@api_view(['POST'])
def verify_otp(request):
    phone = request.data.get('phone')
    otp = request.data.get('otp')
    if not phone or not otp:
        return Response({'error': 'Телефон номер и OTP обязательны'}, status=400)
    voter = get_object_or_404(Voter, phone=phone)
    if not voter.otp_code or voter.otp_code != otp:
        return Response({'error': 'OTP неверный или срок действия истек'}, status=400)
    voter.is_phone_verified = True
    voter.otp_code = None
    voter.save()
    refresh = RefreshToken.for_user(voter)
    return Response({'msg': 'Телефон номер подтвержден.'})

@swagger_auto_schema(method='post', request_body=LoginSerializer)
@api_view(['POST'])
def login_view(request):
    phone = request.data.get('phone')
    password = request.data.get('password')
    voter = authenticate(request, phone=phone, password=password)
    if voter is None or not voter.is_phone_verified:
        return Response({'error': 'Логин или пароль неверный, либо телефон номер не подтвержден'}, status=400)
    refresh = RefreshToken.for_user(voter)
    return Response({
        'msg': 'Успешный вход.',
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    })

@swagger_auto_schema(method='post', request_body=VerifyOtpSerializer)
@api_view(['POST'])
def resend_otp(request):
    phone = request.data.get('phone')
    if not phone:
        return Response({'error': 'Телефон номер обязателен'}, status=400)
    voter = Voter.objects.filter(phone=phone).first()
    if not voter:
        return Response({'error': 'Этот телефон номер еще не зарегистрирован'}, status=404)
    if voter.is_phone_verified:
        return Response({'error': 'Телефон номер уже подтвержден'}, status=400)
    otp = str(random.randint(100000, 999999))
    voter.otp_code = otp
    voter.save()
    send_otp_to_telegram(phone, otp)
    return Response({'msg': 'Новый OTP код отправлен.'}, status=200)

@api_view(['GET'])
def poll_list(request):
    polls = Poll.objects.all()
    data = []
    for poll in polls:
        candidates = poll.candidates.all()
        data.append({
            'id': poll.id,
            'title': poll.title,
            'description': poll.description,
            'candidates': [
                {
                    'id': candidate.id,
                    'name': candidate.name,
                    'info': candidate.info
                } for candidate in candidates
            ]
        })
    return Response(data)

@swagger_auto_schema(method='get')
@api_view(['GET'])
def poll_detail(request, poll_id):
    poll = get_object_or_404(Poll, id=poll_id)
    candidates = poll.candidates.all()
    data = {
        'id': poll.id,
        'title': poll.title,
        'description': poll.description,
        'start_time': poll.start_time,
        'end_time': poll.end_time,
        'candidates': [
            {
                'id': candidate.id,
                'name': candidate.name,
                'info': candidate.info,
                'votes': Vote.objects.filter(candidate=candidate).count()
            } for candidate in candidates
        ]
    }
    return Response(data)
@swagger_auto_schema(method='post', request_body=VoteSerializer)
@api_view(['POST'])
def vote(request):
    if not request.user.is_authenticated:
        return Response({'error': 'Требуется токен'}, status=401)
    poll_id = request.data.get('poll_id')
    candidate_id = request.data.get('candidate_id')
    poll = get_object_or_404(Poll, id=poll_id)

    if poll.end_time and poll.end_time < timezone.now():
        return Response({'error': 'Время голосования по этому опросу истекло'}, status=400)
    candidate = get_object_or_404(Candidate, id=candidate_id, poll=poll)
    voter = request.user
    if Vote.objects.filter(voter=voter, poll=poll).exists():
        return Response({'error': 'Вы уже голосовали в этом опросе'}, status=400)
    Vote.objects.create(voter=voter, poll=poll, candidate=candidate)
    return Response({'msg': 'Голос принят'})

@api_view(['GET'])
def my_votes(request):
    if not request.user.is_authenticated:
        return Response({'error': 'Требуется токен'}, status=401)
    votes = Vote.objects.filter(voter=request.user).select_related('poll', 'candidate')
    data = [
        {
            'poll': v.poll.title,
            'candidate': v.candidate.name,
            'voted_at': v.voted_at
        } for v in votes
    ]
    return Response(data)

@swagger_auto_schema(method='post', request_body=PollCreateSerializer)
@api_view(['POST'])
@permission_classes([IsStaff])
def create_poll(request):
    serializer = PollCreateSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=201)
    return Response(serializer.errors, status=400)

@swagger_auto_schema(method='post', request_body=CandidateCreateSerializer)
@api_view(['POST'])
@permission_classes([IsStaff])
def create_candidate(request):
    serializer = CandidateCreateSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=201)
    return Response(serializer.errors, status=400)


@swagger_auto_schema(method='post', request_body=ResetPasswordSerializer)
@api_view(['POST'])
def reset_password(request):
    serializer = ResetPasswordSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=400)
    user = request.user
    old_password = serializer.validated_data['old_password']
    new_password = serializer.validated_data['new_password']
    if not user or not user.is_authenticated:
        return Response({'error': 'Требуется токен'}, status=401)
    if not user.check_password(old_password):
        return Response({'error': 'Старый пароль неверный'}, status=400)
    user.set_password(new_password)
    user.save()
    return Response({'msg': 'Пароль успешно изменен'})

@swagger_auto_schema(method='post', request_body=ForgotPasswordSendOtpSerializer)
@api_view(['POST'])
def forgot_password(request):
    serializer = ForgotPasswordSendOtpSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=400)
    phone = serializer.validated_data['phone']
    voter = Voter.objects.filter(phone=phone).first()
    if not voter:
        return Response({'error': 'Пользователь с таким номером не найден'}, status=404)
    otp = str(random.randint(100000, 999999))
    voter.otp_code = otp
    voter.save()
    send_otp_to_telegram(phone, otp)
    return Response({'msg': 'OTP код отправлен на Telegram'}, status=200)

@swagger_auto_schema(method='post', request_body=ForgotPasswordConfirmSerializer)
@api_view(['POST'])
def forgot_password_confirm(request):
    serializer = ForgotPasswordConfirmSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=400)
    phone = serializer.validated_data['phone']
    otp = serializer.validated_data['otp']
    new_password = serializer.validated_data['new_password']
    voter = Voter.objects.filter(phone=phone).first()
    if not voter or not voter.otp_code or voter.otp_code != otp:
        return Response({'error': 'OTP неверный или срок действия истек'}, status=400)
    voter.set_password(new_password)
    voter.otp_code = None
    voter.save()
    return Response({'msg': 'Пароль успешно изменен'}, status=200)

@swagger_auto_schema(method='get')
@api_view(['GET'])
def user_info(request):
    if not request.user.is_authenticated:
        return Response({'error': 'Требуется токен'}, status=401)
    user = request.user
    data = {
        'id': user.id,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'phone': user.phone,
        'role': user.get_role_display(),
        'is_phone_verified': user.is_phone_verified,
        'is_active': user.is_active,
        'is_staff': user.is_staff,
    }
    return Response(data)

@swagger_auto_schema(method='patch', request_body=UserUpdateSerializer)
@api_view(['PATCH'])
def update_user_info(request):
    if not request.user.is_authenticated:
        return Response({'error': 'Требуется токен'}, status=401)
    user = request.user
    serializer = UserUpdateSerializer(user, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response({'msg': 'Информация пользователя успешно обновлена'})
    return Response(serializer.errors, status=400)

@swagger_auto_schema(method='delete')
@api_view(['DELETE'])
def delete_user(request):
    if not request.user.is_authenticated:
        return Response({'error': 'Требуется токен'}, status=401)
    user = request.user
    user.delete()
    return Response({'msg': 'Пользователь успешно удален'}, status=204)

@swagger_auto_schema(method='patch')
@api_view(['PATCH'])
def update_poll(request, poll_id):
    if not request.user.is_authenticated or not request.user.is_staff:
        return Response({'error': 'Требуется токен и права staff'}, status=403)
    poll = get_object_or_404(Poll, id=poll_id)
    serializer = PollCreateSerializer(poll, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=200)
    return Response(serializer.errors, status=400)

@swagger_auto_schema(method='patch')
@api_view(['PATCH'])
def update_candidate(request, candidate_id):
    if not request.user.is_authenticated or not request.user.is_staff:
        return Response({'error': 'Требуется токен и права staff'}, status=403)
    candidate = get_object_or_404(Candidate, id=candidate_id)
    serializer = CandidateCreateSerializer(candidate, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=200)
    return Response(serializer.errors, status=400)

@swagger_auto_schema(method='patch')
@api_view(['PATCH'])
@permission_classes([IsStaff])
def update_poll_candidates(request, poll_id):
    poll = get_object_or_404(Poll, id=poll_id)
    candidate_ids = request.data.get('candidate_ids')
    if not isinstance(candidate_ids, list):
        return Response({'error': 'candidate_ids must be a list of candidate IDs'}, status=400)
    candidates = Candidate.objects.filter(id__in=candidate_ids, poll=poll)
    if candidates.count() != len(candidate_ids):
        return Response({'error': 'Some candidates not found in this poll'}, status=400)
    poll.candidates.set(candidates)
    poll.save()
    return Response({'msg': 'Candidates updated for poll'}, status=200)

@swagger_auto_schema(method='delete')
@api_view(['DELETE'])
@permission_classes([IsStaff])
def delete_poll(request, poll_id):
    poll = get_object_or_404(Poll, id=poll_id)
    poll.delete()
    return Response({'msg': 'Poll deleted successfully'}, status=204)

@swagger_auto_schema(method='delete')
@api_view(['DELETE'])
@permission_classes([IsStaff])
def delete_candidate(request, candidate_id):
    candidate = get_object_or_404(Candidate, id=candidate_id)
    candidate.delete()
    return Response({'msg': 'Candidate deleted successfully'}, status=204)

@swagger_auto_schema(method='get')
@api_view(['GET'])
def poll_candidates(request, poll_id):
    poll = get_object_or_404(Poll, id=poll_id)
    candidates = poll.candidates.all()
    data = [
        {
            'id': candidate.id,
            'name': candidate.name,
            'info': candidate.info,
            'votes': Vote.objects.filter(candidate=candidate).count()
        } for candidate in candidates
    ]
    return Response(data)

@swagger_auto_schema(method='get')
@api_view(['GET'])
def poll_votes(request, poll_id):
    poll = get_object_or_404(Poll, id=poll_id)
    votes = Vote.objects.filter(poll=poll).select_related('voter', 'candidate')
    total_votes = votes.count()
    candidate_stats = {}
    last_vote_time = None
    winner_candidates = []
    winner = None

    # Count votes per candidate and track last vote time for tie-break
    for vote in votes.order_by('voted_at'):
        cid = vote.candidate.id
        if cid not in candidate_stats:
            candidate_stats[cid] = {
                'candidate': {
                    'id': vote.candidate.id,
                    'name': vote.candidate.name,
                    'info': vote.candidate.info
                },
                'votes': 0,
                'last_vote_time': None
            }
        candidate_stats[cid]['votes'] += 1
        candidate_stats[cid]['last_vote_time'] = vote.voted_at

    # Prepare stats with percent
    stats = []
    max_votes = 0
    for c in candidate_stats.values():
        c['percent'] = round((c['votes'] / total_votes) * 100, 2) if total_votes else 0
        stats.append({
            **c['candidate'],
            'votes': c['votes'],
            'percent': c['percent']
        })
        if c['votes'] > max_votes:
            max_votes = c['votes']

    # Find all candidates with max votes
    for c in candidate_stats.values():
        if c['votes'] == max_votes:
            winner_candidates.append(c)

    # Tie-break: pick candidate with latest vote
    if winner_candidates:
        winner = max(winner_candidates, key=lambda c: c['last_vote_time'])

    data = {
        'total_votes': total_votes,
        'candidates': stats,
        'winner': winner['candidate'] if winner else None
    }
    return Response(data)

@swagger_auto_schema(method='get')
@api_view(['GET'])
def finished_polls(request):

    now = timezone.now()
    polls = Poll.objects.filter(end_time__lt=now)
    data = []
    for poll in polls:
        candidates = poll.candidates.all()
        data.append({
            'id': poll.id,
            'title': poll.title,
            'description': poll.description,
            'end_time': poll.end_time,
            'candidates': [
                {
                    'id': candidate.id,
                    'name': candidate.name,
                    'info': candidate.info,
                    'votes': Vote.objects.filter(candidate=candidate).count()
                } for candidate in candidates
            ]
        })
    return Response(data)