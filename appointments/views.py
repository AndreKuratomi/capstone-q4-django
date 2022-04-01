from datetime import datetime
from urllib import response
from datetime import date, datetime, time, timedelta
from django.shortcuts import render
from django.core.exceptions import ObjectDoesNotExist
from time import sleep

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
# from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.decorators import authentication_classes, permission_classes

from user.views import ProfessionalsByIdView
from .models import AppointmentsModel
from .serializers import AllAppointmentsSerializer, AppPatientSerializer, AppProfessonalSerializer, AppointmentsSerializer, AppointmentsToUpdateSerializer
from .permissions import AppointmentPermission
from user.models import Patient, Professional, User
from user.serializers import PatientSerializer, ProfessionalSerializer, NewPatientSerializer
from .serializers import AppointmentsSerializer, AppointmentsToUpdateSerializer
from .models import AppointmentsModel
from .permissions import AppointmentPermission
import pywhatkit

# import ipdb


class SpecificPatientView(APIView):

    authentication_classes = [TokenAuthentication]
    permission_classes = [AppointmentPermission]

    def get(self, request, cpf=''):
        try:
            patient = Patient.objects.get(cpf=cpf)

            if patient:
                appointment = AppointmentsModel.objects.filter(patient=patient)
                serializer = AppointmentsSerializer(appointment, many=True)

                return Response(serializer.data, status=status.HTTP_200_OK)

        except Patient.DoesNotExist:
            return Response(
                {"message": "Patient does not exist"}, status=status.HTTP_404_NOT_FOUND
            )


class SpecificProfessionalView(APIView):
    print('***')
    authentication_classes = [TokenAuthentication]
    permission_classes = [AppointmentPermission]

    def get(self, request, council_number=''):
        try:
            professional = Professional.objects.get(council_number=council_number)

            if professional:
                appointment = AppointmentsModel.objects.filter(professional=professional)

                serializer = AppointmentsSerializer(appointment, many=True)

                return Response(serializer.data, status=status.HTTP_200_OK)

        except Professional.DoesNotExist:
            return Response(
                {"message": "Professional not registered"}, status=status.HTTP_404_NOT_FOUND,
            )


class SpecificAppointmentView(APIView):

    authentication_classes = [TokenAuthentication]
    permission_classes = [AppointmentPermission]

    def get(self, request, appointment_id=''):
        try:
            appointment = AppointmentsModel.objects.get(uuid=appointment_id)

            if appointment:

                serializer = AppointmentsSerializer(appointment)

                return Response(serializer.data, status=status.HTTP_200_OK)

        except AppointmentsModel.DoesNotExist:
            return Response(
                {"message": "Appointment not registered"}, status=status.HTTP_404_NOT_FOUND,
            )

    def patch(self, request, appointment_id=''):
        try:
            appointment = AppointmentsModel.objects.get(uuid=appointment_id)

            if appointment:
                serialized = AppointmentsToUpdateSerializer(data=request.data, partial=True)

                if serialized.is_valid():
                    data = {**serialized.validated_data}

                    for key, value in data.items():
                        appointment.__dict__[key] = value

                    appointment.save()

                    updated_appointment = AppointmentsModel.objects.get(uuid=appointment_id)
                    serialized = AppointmentsSerializer(updated_appointment)

                    appointment_date = str(appointment.date.day) + "/" + str(appointment.date.month) + "/" + str(appointment.date.year)

                    appointment_hour = str(appointment.date.hour) + ":" + str(appointment.date.minute)

                    whats_message = f"""

                        ⚠️   *Reagendamento de consulta*
                        *Paciente:* {appointment.patient.name} 
                        *Profissional:* {appointment.professional.name} 
                        *Especialidade:* {appointment.professional.specialty} 
                        *Data:* {appointment_date} 
                        *Horário:* {appointment_hour} 
                        *Local:* Clínica Kenzie Doc 
                        *Endereço:* R. General Mario Tourinho, 1733
                        *Para reagendar/cancelar a consulta, entre em contato com a Kenzie Doc.* 
                    
                    """

                    time_to_send = datetime.now() + timedelta(minutes=1)

                    sleep(10)

                    pywhatkit.sendwhatmsg(f"+55{appointment.patient.phone}", whats_message, time_to_send.hour,time_to_send.minute) 

                    return Response(serialized.data, status=status.HTTP_200_OK)

        except AppointmentsModel.DoesNotExist:
            return Response({'message': 'Appointment does not exist'}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, appointment_id=''):
        try:
            appointment = AppointmentsModel.objects.get(uuid=appointment_id)

            if appointment:

                appointment.delete()

                return Response(status=status.HTTP_204_NO_CONTENT)

        except AppointmentsModel.DoesNotExist:
            return Response({'message': 'Appointment does not exist'}, status=status.HTTP_404_NOT_FOUND)


class TomorrowAppointmentView(APIView):

    authentication_classes = [TokenAuthentication]
    permission_classes = [AppointmentPermission]

    def get(self, request, council_number=''):
        try:
            professional = Professional.objects.get(council_number=council_number)

            if professional:
                now = datetime.now()
                tomorrow = datetime.now().date() + timedelta(days=1)
                end_tomorrow = tomorrow + timedelta(days=1)
                appointments_for_tomorrow = AppointmentsModel.objects.filter(date__range=[tomorrow, end_tomorrow])

                # ipdb.set_trace()
                if appointments_for_tomorrow:
                    for unfinished in appointments_for_tomorrow:
                        serializer = AppointmentsSerializer(unfinished)

                    return Response(serializer.data, status=status.HTTP_200_OK)
                return Response({"message": "No appointments for tomorrow!"}, status=status.HTTP_200_OK)

        except Professional.DoesNotExist:
            return Response({"message": "Professional not registered"}, status=status.HTTP_404_NOT_FOUND)

        except:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class NotFinishedAppointmentView(APIView):

    authentication_classes = [TokenAuthentication]
    permission_classes = [AppointmentPermission]

    def get(self, request):

            not_finished_appointment = AppointmentsModel.objects.filter(finished=False)

            serialized_not_finished = [
                {
                    "uuid": appointment.uuid,
                    "date": appointment.date,
                    "patient": "appointment.patient.name",
                    "professional": appointment.professional.name,
                    "complaint": appointment.complaint,
                    "finished": appointment.finished
                } for appointment in not_finished_appointment
            ]  


            return Response(serialized_not_finished, status=status.HTTP_200_OK)



class CreateAppointment(APIView):

    authentication_classes = [TokenAuthentication]
    permission_classes = [AppointmentPermission]

    def post(self, request):

        professional = Professional.objects.get(council_number=request.data['council_number'])

        patient = Patient.objects.get(cpf=request.data['cpf']) 

        data=request.data

        prof = ProfessionalSerializer(professional)
        # pat = NewPatientSerializer(patient)
        pat = PatientSerializer(patient)

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
            *Paciente:* {patient.name} 
            *Profissional:* {professional.name} 
            *Especialidade:* {professional.specialty} 
            *Data:* {appointment_date} 
            *Horário:* {appointment_hour} 
            *Local:* Clínica Kenzie Doc 
            *Endereço:* R. General Mario Tourinho, 1733
            *Para reagendar/cancelar a consulta, entre em contato com a Kenzie Doc.* 
        
        """

        time_to_send = datetime.now() + timedelta(minutes=1)

        sleep(10)

        pywhatkit.sendwhatmsg(f"+55{patient.phone}", whats_message, time_to_send.hour,time_to_send.minute) 

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    
