import datetime
from django.core.exceptions import ObjectDoesNotExist
from job.models import Job
from shift.models import Shift, VolunteerShift
from volunteer.services import get_volunteer_by_id

def add_shift_hours(v_id, s_id, start_time, end_time):

    is_valid = True
    volunteer_shift = get_volunteer_shift_by_id(v_id, s_id)

    if volunteer_shift:
        volunteer_shift.start_time = start_time
        volunteer_shift.end_time = end_time
        volunteer_shift.save()
    else:
        is_valid = False

    return is_valid

def calculate_working_duration(start_time, end_time):

    start_delta = datetime.timedelta(hours=start_time.hour, minutes=start_time.minute)
    end_delta = datetime.timedelta(hours=end_time.hour, minutes=end_time.minute)
    working_hours = (float((abs(end_delta - start_delta)).seconds) / 60) / 60
    return working_hours

def cancel_shift_registration(v_id, s_id):

    is_valid = True

    if s_id and v_id:
        shift = Shift.objects.get(pk=s_id)
        if shift:
            try:
                obj = VolunteerShift.objects.get(volunteer_id=v_id, shift_id=s_id)
                #remove volunteer from being signed up for this shift
                obj.delete()
                #increment the slots remaining for this shift
                increment_slots_remaining(shift)
            except ObjectDoesNotExist:
                is_valid = False
        else:
            is_valid = False
    else:
        is_valid = False

    return is_valid

def delete_shift_hours(v_id, s_id):

    is_valid = True
    volunteer_shift = get_volunteer_shift_by_id(v_id, s_id)

    if volunteer_shift:
        volunteer_shift.start_time = None
        volunteer_shift.end_time = None
        volunteer_shift.save()
    else:
        is_valid = False

    return is_valid

def edit_shift_hours(v_id, s_id, start_time, end_time):

    is_valid = True
    volunteer_shift = get_volunteer_shift_by_id(v_id, s_id)

    if volunteer_shift:
        volunteer_shift.start_time = start_time
        volunteer_shift.end_time = end_time
    else:
        is_valid = False

    return is_valid
    
def get_shift_by_id(shift_id):
    
    is_valid = True
    result = None

    try:
        shift = Shift.objects.get(pk=shift_id)
    except ObjectDoesNotExist:
        is_valid = False

    if is_valid:
        result = shift

    return result

def get_shifts_by_date(j_id):
    shift_list = Shift.objects.filter(job_id=j_id).order_by('date')
    return shift_list

def get_shifts_signed_up_for(v_id):

    #find a better way to do this (maybe there is a built in way to get a foreign
    #key after a filter
    list = VolunteerShift.objects.filter(volunteer_id=v_id)
    shift_signed_up_list = [] 

    for volunteer_shift in list:
        shift_signed_up_list.append(volunteer_shift.shift)

    #sort by job title, shift date and shift start_time
    shift_signed_up_list.sort(key=lambda x: (x.job.job_title,
                                            x.date,
                                            x.start_time))

    return shift_signed_up_list

def get_volunteer_shift_by_id(v_id, s_id):
    
    is_valid = True
    result = None

    try:
        volunteer_shift = VolunteerShift.objects.get(volunteer_id=v_id, shift_id=s_id)
    except ObjectDoesNotExist:
        is_valid = False

    if is_valid:
        result = volunteer_shift

    return result

def decrement_slots_remaining(shift):
    shift.slots_remaining = shift.slots_remaining - 1
    shift.save()

def has_slots_remaining(shift):

    has_slots = False 

    if shift.slots_remaining >= 1:
        has_slots = True

    return has_slots

def increment_slots_remaining(shift):
    shift.slots_remaining = shift.slots_remaining + 1
    shift.save()

def is_signed_up(v_id, s_id):

    result = True

    volunteer_shift = get_volunteer_shift_by_id(v_id, s_id)
    if not volunteer_shift:
        result = False 

    return result

def register(v_id, s_id):

    is_valid = True

    #a volunteer must not be allowed to register for a shift that they are already registered for
    signed_up = is_signed_up(v_id, s_id)

    if not signed_up:
        volunteer_obj = get_volunteer_by_id(v_id)
        shift_obj = get_shift_by_id(s_id) 

        if volunteer_obj and shift_obj:
            if has_slots_remaining(shift_obj):
                registration_obj = VolunteerShift(volunteer=volunteer_obj, shift=shift_obj)
                registration_obj.save()

                decrement_slots_remaining(shift_obj)
            else:
                is_valid = False
        else:
            is_valid = False
    else:
        is_valid = False

    return is_valid    
