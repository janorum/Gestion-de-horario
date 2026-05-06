from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login
from django.contrib.auth.views import LoginView


class RegistroForm(UserCreationForm):
    """Formulario de registro con campos en español y sin textos de ayuda."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.help_text = None
            field.widget.attrs.update({'class': 'form-control'})
        self.fields['username'].label = 'Usuario'
        self.fields['password1'].label = 'Contraseña'
        self.fields['password2'].label = 'Confirmar contraseña'


class LoginConRegistroView(LoginView):
    """LoginView estándar que inyecta también el formulario de registro vacío."""
    template_name = 'login.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.setdefault('reg_form', RegistroForm())
        ctx.setdefault('active_tab', 'login')
        return ctx


def registro_view(request):
    if request.user.is_authenticated:
        return redirect('horario:ver_horario')

    form = RegistroForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('horario:ver_horario')
        # Errores: volver al login con la pestaña de registro activa
        return render(request, 'login.html', {
            'reg_form': form,
            'active_tab': 'registro',
            'form': AuthenticationForm(),
        })

    return redirect('login')
