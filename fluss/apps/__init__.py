from .organizer.main import entry_with_args as orgainzer_entry

def apps_entry():
    import fire
    fire.Fire({"organizer": orgainzer_entry})

# TODO: add functionality
# - batch cover embedding
# - batch accurip test
# - batch codec change (image and audio)
