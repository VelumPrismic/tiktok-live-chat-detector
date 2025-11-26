from TikTokLive.events import ConnectEvent, CommentEvent

def apply_patch():
    # --- MONKEY PATCH FOR TIKTOKLIVE/BETTERPROTO ISSUE ---
    try:
        from TikTokLive.proto import custom_proto
        
        def _patched_from_user(user, **kwargs):
            data = user.to_pydict(**kwargs)
            # Fix camelCase keys to snake_case
            if 'nickName' in data:
                data['nick_name'] = data.pop('nickName')
            if 'displayId' in data:
                data['display_id'] = data.pop('displayId')
            if 'userImageSurround' in data:
                data['user_image_surround'] = data.pop('userImageSurround')
            if 'fanTicketCount' in data:
                data['fan_ticket_count'] = data.pop('fanTicketCount')
                
            return custom_proto.ExtendedUser(**data)

        custom_proto.from_user = _patched_from_user
        print("TikTokLive Monkey Patch Applied.")
    except Exception as e:
        print(f"Warning: Failed to patch TikTokLive: {e}")
