"""
FSM State Definitions
Defines all conversation states for the bot.
"""

from aiogram.fsm.state import State, StatesGroup


class ProfileStates(StatesGroup):
    """States for nutritionist profile creation/update flow."""
    
    # Waiting for full name input
    waiting_full_name = State()
    
    # Waiting for photo upload
    waiting_photo = State()
    
    # Waiting for bio text
    waiting_bio = State()
    
    # Selecting specializations (multi-select)
    selecting_specializations = State()
    
    # Selecting tags (optional, multi-select)
    selecting_tags = State()
    
    # Confirming rules and restrictions
    confirming_rules = State()
    
    # Final confirmation before submission
    confirming_submission = State()


class ServiceStates(StatesGroup):
    """States for service creation/edit flow."""
    
    # Waiting for service title
    waiting_title = State()
    
    # Waiting for service description (optional)
    waiting_description = State()
    
    # Waiting for duration in minutes
    waiting_duration = State()
    
    # Waiting for price in RUB
    waiting_price = State()
    
    # Confirming service creation
    confirming_service = State()
    
    # Editing existing service - selecting which to edit
    selecting_service = State()
    
    # Editing - waiting for new value
    editing_title = State()
    editing_description = State()
    editing_duration = State()
    editing_price = State()


class SlotStates(StatesGroup):
    """States for availability slot creation flow."""
    
    # Selecting date for new slot
    selecting_date = State()
    
    # Waiting for start time input (HH:MM)
    waiting_start_time = State()
    
    # Selecting slot duration
    selecting_duration = State()
    
    # Confirming slot creation
    confirming_slot = State()
    
    # Selecting slot to delete
    selecting_slot_to_delete = State()


class SupportStates(StatesGroup):
    """States for support message flow."""
    
    # Waiting for support message
    waiting_message = State()

