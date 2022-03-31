from datetime import datetime
from urllib import response
from datetime import date, datetime, time, timedelta
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.decorators import authentication_classes, permission_classes
from .models import AppointmentsModel
from .serializers import AllAppointmentsSerializer, AppPatientSerializer, AppProfessonalSerializer, AppointmentsSerializer
from .permissions import AppointmentPermission
from user.models import Patient, Professional, User
from user.serializers import PatientSerializer, ProfessionalSerializer, NewPatientSerializer
import pywhatkit


class SpecificPatientView(APIView):

    authentication_classes = [TokenAuthentication]
    permission_classes = [AppointmentPermission]

    def get(self, request, cpf):
        try:
            patient = Patient.objects.get(cpf=cpf)

            appointment = AppointmentsModel.objects.filter(patient=patient)

            for appointments in appointment:
                serializer = AppointmentsSerializer(appointments)

            return response(serializer.data, status=status.HTTP_200_OK)

        except ObjectDoesNotExist:
            return response(
                {"message": "Patient does not exist"}, status=status.HTTP_404_NOT_FOUND
            )


class SpecificProfessionalView(APIView):

    authentication_classes = [TokenAuthentication]
    permission_classes = [AppointmentPermission]

    def get(self, request, council_number):
        try:
            professional = Professional.objects.get(council_number=council_number)

            appointment = AppointmentsModel.objects.filter(professional=professional)

            for appointments in appointment:
                serializer = AppointmentsSerializer(appointments)

            return response(serializer.data, status=status.HTTP_200_OK)

        except ObjectDoesNotExist:
            return response(
                {"message": "Professional not registered"},
                status=status.HTTP_404_NOT_FOUND,
            )


class NotFinishedAppointmentView(APIView):

    authentication_classes = [TokenAuthentication]
    permission_classes = [AppointmentPermission]

    def get(self, request):
        try:

            not_finished_appointment = AppointmentsModel.objects.filter(finished=False)

            for unfinished in not_finished_appointment:
                serializer = AppointmentsSerializer(unfinished)

            return response(serializer.data, status=status.HTTP_200_OK)

        except ObjectDoesNotExist:
            return response(
                {"message": "Professional not registered"},
                status=status.HTTP_404_NOT_FOUND,
            )


class CreateAppointment(APIView):

    authentication_classes = [TokenAuthentication]
    permission_classes = [AppointmentPermission]

    def post(self, request):

        professional = Professional.objects.get(council_number=request.data['council_number'])
        
        patient = Patient.objects.get(cpf=request.data['cpf']) 

        data=request.data

        prof = ProfessionalSerializer(professional)
        pat = NewPatientSerializer(patient)

        data['professional'] = prof.data["council_number"]
        data['patient'] = pat.data["cpf"]

        serializer = AppointmentsSerializer(
            data=data
        )
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer.validated_data['professional'] = professional
        serializer.validated_data['patient'] = patient
        appointment = AppointmentsModel.objects.create(**serializer.validated_data)
        serializer = AppointmentsSerializer(appointment)
        
        appointment_date = str(appointment.date.day) + "/" + str(appointment.date.month) + "/" + str(appointment.date.year)

        appointment_hour = str(appointment.date.hour) + ":" + str(appointment.date.minute)

        whats_message = f"""

            ✅  *Confirmação de agendamento de consulta*
            *Paciente:* Nome do paciente
            *Profissional:* {professional.name} 
            *Especialidade:* {professional.specialty} 
            *Data:* {appointment_date} 
            *Horário:* {appointment_hour} 
            *Local:* Clínica Kenzie Doc 
            *Endereço:* R. General Mario Tourinho, 1733
            *Para reagendar/cancelar a consulta, entre em contato com a Kenzie Doc.* 
        
        """

        time_to_send = datetime.now() + timedelta(minutes=1)
        pywhatkit.sendwhatmsg("+5519997416761", whats_message, time_to_send.hour,time_to_send.minute) 

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    