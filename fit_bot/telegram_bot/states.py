from enum import Enum


class States(Enum):
    START = "start"
    STATE_1 = "state_1"
    STATE_2 = "state_2"
    ASK_GENDER = 'ask_gender'
    ASK_AGE = 'ask_age'
    ASK_HEIGHT = 'ask_height'
    ASK_WEIGHT = 'ask_weight'
    ASK_ACTIVITY = 'ask_activity'
    FINISHED = 'finished'
    ASK_INITIALS = 'ask_initials'
    CONTINUE_INITIALS = 'continue_initials'
    ASK_PLACE = 'ask_place'
    ASK_GOAL = 'ask_goal'
    ASK_EXPERIENCE = 'ask_experience'
    WRITE_CALORIES = 'write_calories'
    ADD_REMOVE_CALORIES = 'add_remove_calories'
    MAILING = 'mailing'
    CHOOSING_MAILING_CATEGORY = 'choosing_mailing_category'
    ENTER_TEXT_FOR_MAILING = 'enter_text_for_mailing'
    UPLOAD_VIDEO = 'upload_video'
    CHOOSE_PRODUCT = 'choose_product'
    ASK_PRODUCT_NAME = 'ask_product_name'