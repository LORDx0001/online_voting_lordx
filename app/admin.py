from django.contrib import admin
from .models import Voter, Poll, Candidate, Vote

@admin.register(Voter)
class VoterAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'phone', 'is_phone_verified', 'is_staff', 'is_superuser')

@admin.register(Poll)
class PollAdmin(admin.ModelAdmin):
    list_display = ('title', 'description')

@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ('name', 'poll')

@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ('voter', 'poll', 'candidate', 'voted_at')