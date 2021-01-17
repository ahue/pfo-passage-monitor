from pfo_passage_monitor import motion

def set_label(id, label):
  
    motion.set_event_label(id, label)

    return label, id