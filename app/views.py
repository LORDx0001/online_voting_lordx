import re
import random
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
    ForgotPasswordSendOtpSerializer, ForgotPasswordConfirmSerializer, ChangeNameSerializer,
    ChangePhoneNumberSerializer, ChangePhoneNumberVerifySerializer, ResendOtpSerializer
)
from .permissions import IsStaff
from django.shortcuts import render
import datetime
from django.utils import timezone
from .utils import send_otp_to_telegram
from django.contrib.auth import logout


def home(request):
    return render(request, 'home.html')



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

    existing_voter = Voter.objects.filter(phone=phone).first()
    if existing_voter:
        if not existing_voter.is_phone_verified:
            otp = str(random.randint(100000, 999999))
            existing_voter.otp_code = otp
            existing_voter.set_password(password)  
            existing_voter.save()
            send_otp_to_telegram(phone, otp)
            return Response({'msg': 'Телефон номер еще не подтвержден. Новый OTP код отправлен.'}, status=200)
        else:
            return Response({'error': 'Этот телефон номер уже зарегистрирован'}, status=400)

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

@swagger_auto_schema(method='post', request_body=ResendOtpSerializer)
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

@swagger_auto_schema(method= 'get')
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
            'start_time':  f"{poll.start_date}, {poll.start_time}" ,
            'end_time': f"{poll.end_date}, {poll.end_time}" ,
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
@permission_classes([])
def vote(request):
    poll_id = request.data.get('poll_id')
    candidate_id = request.data.get('candidate_id')

    poll = get_object_or_404(Poll, id=poll_id)
    candidate = get_object_or_404(Candidate, id=candidate_id, poll=poll)

    now = timezone.now()

    if poll.start_date and poll.start_time:
        start_dt = timezone.make_aware(datetime.datetime.combine(poll.start_date, poll.start_time))
        if now < start_dt:
            return Response({'error': 'Голосование еще не началось'}, status=400)

    if poll.end_date and poll.end_time:
        end_dt = timezone.make_aware(datetime.datetime.combine(poll.end_date, poll.end_time))
        if now > end_dt:
            return Response({'error': 'Время голосования истекло'}, status=400)

    if Vote.objects.filter(voter=request.user, poll=poll).exists():
        return Response({'error': 'Вы уже голосовали в этом опросе'}, status=400)

    Vote.objects.create(voter=request.user, poll=poll, candidate=candidate)
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
        data= serializer.validated_data
        start_date = data.get('start_date')
        start_time = data.get('start_time')
        end_date = data.get('end_date')
        end_time = data.get('end_time')
        if start_time and end_time and start_time >= end_time:
            return Response({'error': 'Время начала должно быть раньше времени окончания'}, status=400)
        Poll.objects.create(
            title=data['title'],
            description=data['description'],
            start_date=start_date,
            start_time=start_time,
            end_date=end_date,
            end_time=end_time
        )

        return Response(serializer.data, status=201)
    return Response(serializer.errors, status=400)

@swagger_auto_schema(method='post', request_body=CandidateCreateSerializer)
@api_view(['POST'])
@permission_classes([IsStaff])
def create_candidate(request):
    serializer = CandidateCreateSerializer(data=request.data)
    if serializer.is_valid():
        poll = serializer.validated_data.get('poll')

        if poll and poll.end_date and poll.end_time:
            import datetime
            from django.utils import timezone

            end_dt = datetime.datetime.combine(poll.end_date, poll.end_time)
            end_dt = timezone.make_aware(end_dt)
            if timezone.now() > end_dt:
                return Response({'error': 'Этот опрос завершен. Добавление кандидатов невозможно.'}, status=400)

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

@swagger_auto_schema(method='patch', request_body=ChangeNameSerializer)
@api_view(['PATCH'])
def change_name(request):
    if not request.user.is_authenticated:
        return Response({'error': 'Требуется токен'}, status=401)
    user = request.user
    serializer = ChangeNameSerializer(user, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response({'msg': 'Имя пользователя успешно обновлено'})
    return Response(serializer.errors, status=400)

@swagger_auto_schema(method='patch', request_body=ChangePhoneNumberSerializer)
@api_view(['PATCH'])
def change_phone(request):
    if not request.user.is_authenticated:
        return Response({'error': 'Требуется токен'}, status=401)
    user = request.user
    serializer = ChangePhoneNumberSerializer(instance=user, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    new_phone = serializer.validated_data['phone']
    phone_pattern = r'^\+998\d{9}$'
    if not re.match(phone_pattern, new_phone):
        return Response({'error': 'Телефон номер должен начинаться с +998 и состоять из 13 символов. Например: +998901234567'}, status=400)
    if user.phone == new_phone:
        return Response({'error': 'Yangi telefon raqam eski raqam bilan bir xil bo‘lishi mumkin emas'}, status=400)
    if Voter.objects.filter(phone=new_phone, is_phone_verified=True):
        return Response({'error': 'Bu telefon raqam allaqachon boshqa foydalanuvchi tomonidan tasdiqlangan'}, status=400)
    otp = str(random.randint(100000, 999999))
    user.new_phone = new_phone
    user.phone_change_otp = otp
    user.save()
    send_otp_to_telegram(user.phone, otp)
    return Response({'msg': 'Telefon raqamni o‘zgartirish uchun OTP eski raqamga yuborildi'})



@swagger_auto_schema(method='post', request_body=ChangePhoneNumberVerifySerializer)
@api_view(['POST'])
def verify_new_phone(request):
    if not request.user.is_authenticated:
        return Response({'error': 'Требуется токен'}, status=401)
    user = request.user
    otp = request.data.get('otp')
    if not otp:
        return Response({'error': 'OTP talab qilinadi'}, status=400)
    if not user.phone_change_otp or user.phone_change_otp != otp:
        return Response({'error': 'OTP noto‘g‘ri yoki muddati o‘tgan'}, status=400)
    if not user.new_phone:
        return Response({'error': 'Yangi telefon raqam topilmadi'}, status=400)
    
    if Voter.objects.filter(phone=user.new_phone, is_phone_verified=True).exclude(id=user.id).exists():
        return Response({'error': 'Bu telefon raqam allaqachon boshqa foydalanuvchi tomonidan tasdiqlangan'}, status=400)
    
    user.phone = user.new_phone
    user.new_phone = None
    user.phone_change_otp = None
    user.is_phone_verified = False  
    user.save()
    otp2 = str(random.randint(100000, 999999))
    user.otp_code = otp2
    user.save()
    send_otp_to_telegram(user.phone, otp2)

    logout(request)

    return Response({'msg': 'Phone number changed successfully. You have been logged out. Please verify your new number.'})

@swagger_auto_schema(method='delete')
@api_view(['DELETE'])
def delete_user(request):
    if not request.user.is_authenticated:
        return Response({'error': 'Требуется токен'}, status=401)
    user = request.user
    user.delete()
    return Response({'msg': 'Пользователь успешно удален'}, status=204)

@swagger_auto_schema(method='patch',request_body=PollCreateSerializer)
@api_view(['PATCH'])
def update_poll(request, poll_id):
    if not request.user.is_authenticated or not request.user.is_staff:
        return Response({'error': 'Требуется токен и права staff'}, status=403)
    poll = get_object_or_404(Poll, id=poll_id)
    serializer = PollCreateSerializer(poll, data=request.data, partial=True)
    if serializer.is_valid():
        data = serializer.validated_data
        poll.title = data.get('title', poll.title)
        poll.description = data.get('description', poll.description)
        poll.start_date = data.get('start_date', poll.start_date)
        poll.start_time = data.get('start_time', poll.start_time)
        poll.end_date = data.get('end_date', poll.end_date)
        poll.end_time = data.get('end_time', poll.end_time)
        if poll.start_time and poll.end_time and poll.start_time >= poll.end_time:
            return Response({'error': 'Время начала должно быть раньше времени окончания'}, status=400)
        poll.save()
        return Response(serializer.data, status=200)
    return Response(serializer.errors, status=400)

@swagger_auto_schema(method='patch', request_body=CandidateCreateSerializer)
@api_view(['PATCH'])
@permission_classes([IsStaff])
def update_candidate(request, candidate_id):
    candidate = get_object_or_404(Candidate, id=candidate_id)

    poll_id = request.data.get('poll')
    poll = get_object_or_404(Poll, id=poll_id) if poll_id else candidate.poll

    if poll.end_date and poll.end_time:
        import datetime
        from django.utils import timezone

        end_dt = datetime.datetime.combine(poll.end_date, poll.end_time)
        end_dt = timezone.make_aware(end_dt)

        if timezone.now() > end_dt:
            return Response({'error': 'Кандидатов нельзя добавить или переместить в завершенный опрос'}, status=400)

    serializer = CandidateCreateSerializer(candidate, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=200)

    return Response(serializer.errors, status=400)




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

    for c in candidate_stats.values():
        if c['votes'] == max_votes:
            winner_candidates.append(c)

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
    all_polls = Poll.objects.all()
    data = []

    for poll in all_polls:
        if poll.end_date and poll.end_time:
            end_datetime = datetime.datetime.combine(poll.end_date, poll.end_time)
            end_datetime = timezone.make_aware(end_datetime)

            if now > end_datetime:
                candidates = poll.candidates.all()
                total_votes = Vote.objects.filter(poll=poll).count()

                # 1. Top vote count
                candidate_votes = {}
                for c in candidates:
                    candidate_votes[c.id] = Vote.objects.filter(candidate=c).count()

                if candidate_votes:
                    max_vote = max(candidate_votes.values())
                    top_candidates = [cid for cid, v in candidate_votes.items() if v == max_vote]

                    # 2. Break tie using latest vote
                    if len(top_candidates) > 1:
                        latest_vote = Vote.objects.filter(
                            candidate__poll=poll,
                            candidate__id__in=top_candidates
                        ).order_by('-voted_at').first()
                        winner_id = latest_vote.candidate.id if latest_vote else None
                    else:
                        winner_id = top_candidates[0]
                else:
                    winner_id = None

                candidate_data = []
                for candidate in candidates:
                    vote_count = candidate_votes.get(candidate.id, 0)
                    percentage = (vote_count / total_votes) * 100 if total_votes > 0 else 0

                    candidate_data.append({
                        'id': candidate.id,
                        'name': candidate.name,
                        'info': candidate.info,
                        'votes': vote_count,
                        'percentage': f"{percentage:.2f}%",
                        'winner': candidate.id == winner_id
                    })

                data.append({
                    'id': poll.id,
                    'title': poll.title,
                    'description': poll.description,
                    'end_date': poll.end_date,
                    'end_time': poll.end_time,
                    'total_votes': total_votes,
                    'candidates': candidate_data
                })

    return Response(data)

