from nextcord import Intents
from utils.terminal import getlogger

logger = getlogger()

VALID_FLAGS = Intents.VALID_FLAGS
VALID_FLAGS['all'] = Intents.all().value
VALID_FLAGS['default'] = Intents.default().value

def getintents(flags : list | str | int | None = Intents.default()):
    if flags is None: flags = Intents.default()

    if isinstance(flags,Intents):
        logger.warning(f'No intents specified will be used the default intents configuration')
        return flags
    if isinstance(flags, list) and len(flags) > 0:
        intents = Intents.none()
        for flag in flags:
            try:
                getattr(intents,flag)
            except AttributeError: 
                logger.warning(f'Invalid intents flag \'{flag}\'')

            try:
                setattr(intents,flag,True)
                logger.info(f'setting intent flag \'{flag}\'')
            except AttributeError:
                logger.warning(f'flag \'{flag}\' can only be specified via string like \"{flag}\"')
        logger.info(f'Setting intents from list: {flags}')
    elif isinstance(flags, str):
        logger.info(f"Setting intents from flag: \"{flags}\"")
        intents = Intents._from_value(VALID_FLAGS.get(flags,Intents.default().value))
    elif isinstance(flags, int):
        logger.info(f"Setting intents from value: {flags}")
        intents = Intents._from_value(flags)
    else:
        logger.warning(f'Intents not specified correctly will be used default intents configuration')
        intents = Intents.default()
    logger.info(f"intents final value: {intents.value}")
    
    return intents