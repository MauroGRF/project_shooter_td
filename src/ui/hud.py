from direct.gui.OnscreenText import OnscreenText


class HUD:
    def __init__(self, game):
        self.game = game
        self.elements = []
        self.effect_labels = {}

        self.life_label = OnscreenText(
            text="HP: 100",
            pos=(-1.2, 0.9),
            scale=0.06,
            fg=(1, 0.2, 0.2, 1),
            align=0,
            mayChange=True,
        )
        self.elements.append(self.life_label)

        self.stamina_label = OnscreenText(
            text="STA: 100",
            pos=(-1.2, 0.82),
            scale=0.045,
            fg=(0.2, 1, 0.2, 1),
            align=0,
            mayChange=True,
        )
        self.elements.append(self.stamina_label)

        self.dash_label = OnscreenText(
            text="DASH: READY",
            pos=(-1.2, 0.74),
            scale=0.045,
            fg=(1, 1, 1, 1),
            align=0,
            mayChange=True,
        )
        self.elements.append(self.dash_label)

        self.parry_label = OnscreenText(
            text="PARRY: 0",
            pos=(-1.2, 0.66),
            scale=0.045,
            fg=(0.6, 0.8, 1, 1),
            align=0,
            mayChange=True,
        )
        self.elements.append(self.parry_label)

        self.weapon_label = OnscreenText(
            text="WPN: melee",
            pos=(-1.2, 0.58),
            scale=0.045,
            fg=(1, 0.9, 0.4, 1),
            align=0,
            mayChange=True,
        )
        self.elements.append(self.weapon_label)

        self.score_label = OnscreenText(
            text="SCORE: 0",
            pos=(0, 0.9),
            scale=0.06,
            fg=(1, 1, 1, 1),
            align=0,
            mayChange=True,
        )
        self.elements.append(self.score_label)

        self.coins_label = OnscreenText(
            text="COINS: 0",
            pos=(0, 0.82),
            scale=0.05,
            fg=(1.0, 0.85, 0.2, 1),
            align=0,
            mayChange=True,
        )
        self.elements.append(self.coins_label)

        self.keys_label = OnscreenText(
            text="KEYS: 0",
            pos=(0, 0.74),
            scale=0.05,
            fg=(1.0, 0.0, 0.6, 1),
            align=0,
            mayChange=True,
        )
        self.elements.append(self.keys_label)

        self.ammo_label = OnscreenText(
            text="AMMO: ∞",
            pos=(1.2, 0.9),
            scale=0.06,
            fg=(0.2, 0.8, 1, 1),
            align=0,
            mayChange=True,
        )
        self.elements.append(self.ammo_label)

    def show(self):
        for elem in self.elements:
            elem.show()

    def hide(self):
        for elem in self.elements:
            elem.hide()

    def update(self, dt):
        gameplay = self.game.state_machine.get_state("gameplay")
        if not gameplay or not gameplay.level:
            return

        player = gameplay.level.player
        if player:
            self.life_label.setText(f"HP: {int(player.life)}")
            self.score_label.setText(f"SCORE: {int(player.score)}")
            self.coins_label.setText(f"COINS: {int(player.coins)}")
            if hasattr(player, 'keys'):
                self.keys_label.setText(f"KEYS: {int(player.keys)}")
            if hasattr(player, 'stamina'):
                self.stamina_label.setText(f"STA: {int(player.stamina)}")
            if hasattr(player, 'dash_cooldown_timer'):
                if player.is_dashing:
                    self.dash_label.setText("DASH: DASH!")
                elif player.dash_cooldown_timer > 0:
                    self.dash_label.setText(f"DASH: {player.dash_cooldown_timer:.1f}s")
                else:
                    self.dash_label.setText("DASH: READY")
            if hasattr(player, 'parries'):
                if player.is_parrying:
                    self.parry_label.setText("PARRY: ACTIVE!")
                else:
                    self.parry_label.setText(f"PARRY: {int(player.parries)}")
            if hasattr(player, 'weapons'):
                weapon = player.weapons.get(player.selected_weapon, {})
                name = weapon.get('name', player.selected_weapon)
                cd_text = ""
                if weapon.get('type') == 'melee':
                    if getattr(player, 'melee_cooldown_timer', 0) > 0:
                        cd_text = f" ({player.melee_cooldown_timer:.1f}s)"
                    elif hasattr(player, 'melee_state') and player.melee_state is not None:
                        cd_text = " (SWING)"
                else:
                    if player.shoot_cooldown > 0:
                        cd_text = f" ({player.shoot_cooldown:.1f}s)"
                self.weapon_label.setText(f"WPN: {name}{cd_text}")
            if hasattr(player, 'ammo_mode'):
                mode = player.ammo_mode
                weapon = player.weapons.get(player.selected_weapon, {})
                if weapon.get('type') == 'melee' or mode == 'infinite':
                    self.ammo_label.setText(f"{mode.upper()} - AMMO: ∞")
                else:
                    current = player.weapon_ammo.get(player.selected_weapon, 0)
                    total = weapon.get('ammo', 999)
                    if current <= 0:
                        self.ammo_label.setText(f"{mode.upper()} - AMMO: {current}/{total} RELOAD (L)")
                    else:
                        self.ammo_label.setText(f"{mode.upper()} - AMMO: {current}/{total}")
            if hasattr(player, 'status_effects'):
                self._update_effect_labels(player)

    def _update_effect_labels(self, player):
        active = []
        for effect in player.status_effects.effects:
            active.append((effect.name, max(0.0, effect.remaining)))

        for name in list(self.effect_labels.keys()):
            if not any(n == name for n, _ in active):
                label = self.effect_labels.pop(name)
                label.destroy()
                if label in self.elements:
                    self.elements.remove(label)

        for i, (name, remaining) in enumerate(active):
            label = self.effect_labels.get(name)
            if label is None:
                label = OnscreenText(
                    text="",
                    pos=(1.2, 0.84 - i * 0.07),
                    scale=0.045,
                    fg=(1, 0.85, 0.3, 1),
                    align=1,
                    mayChange=True,
                )
                self.effect_labels[name] = label
                self.elements.append(label)
            else:
                label.setPos(1.2, 0.84 - i * 0.07)
            label.setText(f"{name.upper()} ({remaining:.1f}s)")

    def destroy(self):
        for elem in self.elements:
            elem.destroy()
        self.elements.clear()
        self.effect_labels.clear()
