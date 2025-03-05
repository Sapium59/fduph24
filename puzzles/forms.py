import re
import unicodedata

from django import forms
from django.contrib.auth.models import User
from django.core.validators import validate_email
from django.utils.translation import gettext as _

from puzzles.models import (
    Team,
    TeamMember,
    Survey,
    Hint,
)


def looks_spammy(s):
    # do not allow names that are only space or control characters
    if all(unicodedata.category(c).startswith(('Z', 'C')) for c in s): return True
    return re.search('https?://', s, re.IGNORECASE) is not None

class RegisterForm(forms.Form):
    team_id = forms.CharField(
        label='队伍用户名',
        max_length=100,
        help_text=(
            '登录时所用的用户名，应简短且不含特殊字符。'
        ),
    )
    team_name = forms.CharField(
        label='队伍展示名',
        max_length=200,
        help_text=(
            '在团队列表展示的队伍名，您可以在此略整小活。'
        ),
    )
    password = forms.CharField(
        label='队伍密码',
        widget=forms.PasswordInput,
        help_text='登录时所用的密码，在整个队伍内共享。',
    )
    password2 = forms.CharField(
        label='再次输入队伍密码',
        widget=forms.PasswordInput,
    )

    def clean(self):
        cleaned_data = super(RegisterForm, self).clean()
        team_id = cleaned_data.get('team_id')
        password = cleaned_data.get('password')
        password2 = cleaned_data.get('password2')
        team_name = cleaned_data.get('team_name')

        if not team_name or looks_spammy(team_name):
            raise forms.ValidationError(
                '不合法的用户名，请重选。'
            )

        if password != password2:
            raise forms.ValidationError(
                '两次输入密码不匹配，请检查。'
            )

        if User.objects.filter(username=team_id).exists():
            raise forms.ValidationError(
                '用户名已被占用，请重选。'
            )

        if Team.objects.filter(team_name=team_name).exists():
            raise forms.ValidationError(
                '展示名已被占用，请重选。'
            )

        return cleaned_data


def validate_team_member_email_unique(email):
    if TeamMember.objects.filter(email=email).exists():
        raise forms.ValidationError(
            '此邮箱已被使用，请检查。'
        )

class TeamMemberForm(forms.Form):
    name = forms.CharField(label='成员名（必填）', max_length=200)
    email = forms.EmailField(
        label='邮箱（选填）',
        max_length=200,
        required=False,
        validators=[validate_email, validate_team_member_email_unique],
    )


def validate_team_emails(formset):
    emails = []
    for form in formset.forms:
        name = form.cleaned_data.get('name')
        if not name:
            raise forms.ValidationError('所有成员都需要有成员名。')
        if looks_spammy(name):
            raise forms.ValidationError('不合法的成员名，请重选。')
        email = form.cleaned_data.get('email')
        if email:
            emails.append(email)
    if not emails:
        raise forms.ValidationError('注册时需要提供至少一名成员的邮箱。')
    if len(emails) != len(set(emails)):
        raise forms.ValidationError('成员的邮箱不得重复。')
    return emails

class TeamMemberFormset(forms.BaseFormSet):
    def clean(self):
        if any(self.errors):
            return
        validate_team_emails(self)

class TeamMemberModelFormset(forms.models.BaseModelFormSet):
    def clean(self):
        if any(self.errors):
            return
        emails = validate_team_emails(self)
        if (
            TeamMember.objects
            .exclude(team=self.data['team'])
            .filter(email__in=emails)
            .exists()
        ):
            raise forms.ValidationError(
                '此邮箱已被使用，请检查。'
            )


class SubmitAnswerForm(forms.Form):
    answer = forms.CharField(
        label='提交答案',
        max_length=500,
        widget=forms.TextInput(attrs={'autofocus': True}),
    )


class RequestHintForm(forms.Form):
    hint_question = forms.CharField(
        label=(
            '尽可能详细地描述你的当前进展和需要的提示'
        ),
        widget=forms.Textarea,
    )

    def __init__(self, team, *args, **kwargs):
        super(RequestHintForm, self).__init__(*args, **kwargs)
        notif_choices = [('all', '所有成员'), ('none', '不发送')]
        notif_choices.extend(team.get_emails(with_names=True))
        self.fields['notify_emails'] = forms.ChoiceField(
            label='提示收到回复时，发送邮件至',
            choices=notif_choices
        )


class HintStatusWidget(forms.Select):
    def get_context(self, name, value, attrs):
        self.choices = []
        for (option, desc) in Hint.STATUSES:
            if option == Hint.NO_RESPONSE:
                if value != Hint.NO_RESPONSE: continue
            elif option == Hint.ANSWERED:
                if value == Hint.OBSOLETE: continue
                if self.is_followup:
                    desc += '（追问）'
            elif option == Hint.REFUNDED:
                if value == Hint.OBSOLETE: continue
                if self.is_followup:
                    desc += '（关闭）'
            elif option == Hint.OBSOLETE:
                if value != Hint.OBSOLETE: continue
            self.choices.append((option, desc))
        if value == Hint.NO_RESPONSE:
            value = Hint.ANSWERED
            attrs['style'] = 'background-color: #ff3'
        return super(HintStatusWidget, self).get_context(name, value, attrs)

class AnswerHintForm(forms.ModelForm):
    class Meta:
        model = Hint
        fields = ('response', 'status')
        widgets = {'status': HintStatusWidget}


class SurveyForm(forms.ModelForm):
    class Meta:
        model = Survey
        exclude = ('team', 'puzzle', 'submitted_datetime')


# This form is a customization of forms.PasswordResetForm
class PasswordResetForm(forms.Form):
    team_id = forms.CharField(label='队伍用户名', max_length=100)

    def clean(self):
        cleaned_data = super(PasswordResetForm, self).clean()
        team_id = cleaned_data.get('team_id')
        team = Team.objects.filter(user__username=team_id).first()
        if team is None:
            raise forms.ValidationError('没有队伍使用这个用户名。')
        cleaned_data['team'] = team
        return cleaned_data
