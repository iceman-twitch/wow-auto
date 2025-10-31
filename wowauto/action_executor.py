"""Action execution for keyboard and mouse control."""
import asyncio
import random
from typing import Any, Dict, List, Optional

try:
    from pynput.keyboard import Controller as KeyboardController
    from pynput.mouse import Controller as MouseController
except Exception:
    KeyboardController = None
    MouseController = None

from .key_parser import parse_key, parse_button


class ActionExecutor:
    """Executes keyboard and mouse actions."""
    
    def __init__(self, dry_run: bool = False):
        """
        Initialize action executor.
        
        Args:
            dry_run: If True, print actions instead of executing them
        """
        self.dry_run = dry_run
        self._last_mouse_pos: Optional[tuple] = None
        
        if not dry_run:
            if KeyboardController is None or MouseController is None:
                raise RuntimeError("pynput is required. Install with: pip install pynput")
            self.kb = KeyboardController()
            self.ms = MouseController()
        else:
            self.kb = None
            self.ms = None
    
    def _check_chance(self, action: Dict[str, Any]) -> bool:
        """Check if action should execute based on chance (1-100). Returns True if no chance specified."""
        chance = action.get("chance")
        if chance is None:
            return True
        chance = int(chance)
        if chance <= 0:
            return False
        if chance >= 100:
            return True
        return random.randint(1, 100) <= chance
    
    async def execute_action(self, action: Dict[str, Any]):
        """Execute a single action."""
        # Check chance - skip action if chance fails
        if not self._check_chance(action):
            if self.dry_run:
                chance = action.get("chance", 100)
                print(f"[dry] skipping action due to chance ({chance}%)")
            return
        
        atype = str(action.get("type", "key")).lower()
        
        if atype == "wait":
            await self._execute_wait(action)
        elif atype == "superwait":
            await self._execute_superwait(action)
        elif atype == "key":
            await self._execute_key(action)
        elif atype == "mouse":
            await self._execute_mouse(action)
        elif atype == "repeat":
            await self._execute_repeat(action)
        else:
            if self.dry_run:
                chance = action.get("chance", 100)
                print(f"[dry] unknown action type: {atype} [chance: {chance}%]")
            else:
                raise ValueError(f"Unknown action type: {atype}")
        
        # per-action delay with randomness: delay to delay*1.1
        delay = float(action.get("delay", 0))
        if delay:
            delay_random = delay * random.uniform(1.0, 1.1)
            if self.dry_run:
                print(f"[dry] sleep {delay_random:.3f}s (original delay: {delay}s)")
    
    async def _execute_wait(self, action: Dict[str, Any]):
        """Execute wait action with randomness."""
        secs = float(action.get("seconds", 0))
        # Add randomness: ±10% variation
        secs_random = secs * random.uniform(0.9, 1.1)
        if self.dry_run:
            chance = action.get("chance", 100)
            print(f"[dry] wait {secs_random:.3f}s (original: {secs}s) [chance: {chance}%]")
        else:
            await asyncio.sleep(secs_random)
    
    async def _execute_superwait(self, action: Dict[str, Any]):
        """Execute superwait action without randomness."""
        secs = float(action.get("seconds", 0))
        # No randomness - use exact time
        if self.dry_run:
            chance = action.get("chance", 100)
            print(f"[dry] superwait {secs}s (exact, no randomness) [chance: {chance}%]")
        else:
            await asyncio.sleep(secs)
    
    async def _execute_key(self, action: Dict[str, Any]):
        """Execute keyboard action."""
        action_type = str(action.get("action", "press")).lower()
        key_raw = action.get("key")
        key = parse_key(key_raw)
        duration = action.get("duration")  # Exact duration if specified
        
        # Add human-like delay before key action: 0.05-0.09s
        pre_delay = random.uniform(0.05, 0.09)
        
        if self.dry_run:
            chance = action.get("chance", 100)
            duration_info = f" duration={duration}s" if duration else ""
            print(f"[dry] key {action_type} {key_raw} (pre-delay: {pre_delay:.3f}s){duration_info} [chance: {chance}%]")
        else:
            if action_type == "press":
                self.kb.press(key)
                if duration is not None:
                    # Use exact duration (no randomness)
                    await asyncio.sleep(float(duration))
                else:
                    # Use random key hold time
                    await asyncio.sleep(random.uniform(0.01, 0.03))
                self.kb.release(key)
            elif action_type == "down":
                self.kb.press(key)
            elif action_type == "up":
                self.kb.release(key)
            elif action_type == "hold":
                if duration is not None:
                    # Use exact duration (no randomness)
                    dur = float(duration)
                else:
                    # Fall back to old behavior with randomness
                    dur = float(action.get("duration", 0))
                self.kb.press(key)
                await asyncio.sleep(dur)
                self.kb.release(key)
            else:
                raise ValueError(f"Unknown key action: {action_type}")
    
    async def _smooth_move_mouse(self, from_x: int, from_y: int, to_x: int, to_y: int):
        """
        Smoothly move mouse from current position to target position.
        Uses Bezier curve for natural movement.
        """
        # Calculate distance
        distance = ((to_x - from_x) ** 2 + (to_y - from_y) ** 2) ** 0.5
        
        # Determine number of steps based on distance (more steps for longer distances)
        steps = max(10, int(distance / 10))  # At least 10 steps, or 1 step per 10 pixels
        
        # Add slight curve to movement (Bezier control point)
        # Random control point offset for natural variation
        mid_x = (from_x + to_x) / 2 + random.randint(-20, 20)
        mid_y = (from_y + to_y) / 2 + random.randint(-20, 20)
        
        # Move mouse in smooth steps along curved path
        for i in range(steps + 1):
            t = i / steps  # 0.0 to 1.0
            
            # Quadratic Bezier curve formula
            x = int((1-t)**2 * from_x + 2*(1-t)*t * mid_x + t**2 * to_x)
            y = int((1-t)**2 * from_y + 2*(1-t)*t * mid_y + t**2 * to_y)
            
            self.ms.position = (x, y)
            
            # Small delay between steps (faster at beginning/end, slower in middle)
            # Simulate human acceleration/deceleration
            if i < steps:
                delay = random.uniform(0.001, 0.003)  # 1-3ms between steps
                await asyncio.sleep(delay)
    
    async def _execute_mouse(self, action: Dict[str, Any]):
        """Execute mouse action."""
        action_type = str(action.get("action", "click")).lower()
        btn = parse_button(action.get("button", "left"))
        x = action.get("x")
        y = action.get("y")
        clicks = int(action.get("clicks", 1))
        interval = float(action.get("interval", 0.0))
        duration = action.get("duration")  # Exact duration if specified
        
        if self.dry_run:
            chance = action.get("chance", 100)
            duration_info = f" duration={duration}s" if duration else ""
            print(f"[dry] mouse {action_type} {btn} to ({x},{y}) clicks={clicks}{duration_info} [chance: {chance}%]")
        else:
            # Step 1: Move mouse smoothly if needed
            # Add 1-2 pixel random offset for human-like variation
            mouse_moved = False
            if x is not None and y is not None:
                # Add random offset: -2 to +2 pixels for both x and y
                offset_x = random.randint(-2, 2)
                offset_y = random.randint(-2, 2)
                target_x = int(x) + offset_x
                target_y = int(y) + offset_y
                
                # Get current mouse position
                current_x, current_y = self.ms.position
                
                # Only move if position changed
                if (current_x, current_y) != (target_x, target_y):
                    # Smooth move from current position to target
                    await self._smooth_move_mouse(current_x, current_y, target_x, target_y)
                    self._last_mouse_pos = (target_x, target_y)
                    mouse_moved = True
            
            # Step 2: If mouse was moved, wait briefly before clicking (human reaction time)
            if mouse_moved:
                move_settle_delay = random.uniform(0.02, 0.05)
                await asyncio.sleep(move_settle_delay)
            
            # Step 3: Now perform the mouse action (click, hold, etc.)
            if action_type == "click":
                for i in range(clicks):
                    self.ms.press(btn)
                    if duration is not None:
                        # Use exact duration (no randomness)
                        await asyncio.sleep(float(duration))
                    else:
                        # Use random click hold time
                        await asyncio.sleep(random.uniform(0.01, 0.03))
                    self.ms.release(btn)
                    if interval and i < clicks - 1:
                        interval_random = interval * random.uniform(0.9, 1.1)
                        await asyncio.sleep(interval_random)
                    elif i < clicks - 1:
                        # Small delay between clicks even without explicit interval
                        await asyncio.sleep(random.uniform(0.05, 0.09))
            elif action_type == "down":
                self.ms.press(btn)
            elif action_type == "up":
                self.ms.release(btn)
            elif action_type == "hold":
                if duration is not None:
                    # Use exact duration (no randomness)
                    dur = float(duration)
                else:
                    # Fall back to old behavior with randomness
                    dur = float(action.get("duration", 0))
                    dur = dur * random.uniform(0.9, 1.1)
                self.ms.press(btn)
                await asyncio.sleep(dur)
                self.ms.release(btn)
            else:
                raise ValueError(f"Unknown mouse action: {action_type}")
    
    async def _execute_repeat(self, action: Dict[str, Any]):
        """Execute repeat action."""
        every = float(action.get("every", 0))
        count = action.get("count", None)
        inner = action.get("actions", [])
        runs = int(count) if count is not None else None
        i = 0
        while runs is None or i < runs:
            for inner_action in inner:
                await self.execute_action(inner_action)
            i += 1
            if every <= 0:
                break
            every_random = every * random.uniform(0.9, 1.1)
            await asyncio.sleep(every_random)
