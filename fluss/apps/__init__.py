from .organizer.main import entry_with_args as orgainzer_entry

def apps_entry():
    import fire
    fire.Fire({"organizer": orgainzer_entry})
