use std::collections::HashMap;

struct Board {
    board: [usize; 0x10],
    moves: Vec<usize>,
    max_moves: usize,
    move_number: usize,

    empt_idx: usize,


    solved_grid: [usize; 0x10],

    fixed_moves: HashMap<usize, usize>,

    move_limit: [isize; 0x10]
}

impl Board {
    pub fn new(board: [usize; 0x10]) -> Self {
        let empt_idx: usize = board.iter().position(|&r| r == 0).unwrap().try_into().unwrap();
        let all_moves: [usize; 0x36] = [
            0x0d, 0x03, 0x02, 0x0e, 0x0f, 0x09, 0x07, 0x0e, 0x0d, 0x06, 0x03, 0x02, 0x07, 0x02, 0x08, 0x0e,
            0x07, 0x04, 0x04, 0x03, 0x0d, 0x04, 0x0c, 0x03, 0x0f, 0x02, 0x0a, 0x05, 0x09, 0x01, 0x06, 0x0a,
            0x0b, 0x02, 0x05, 0x0c, 0x0e, 0x0b, 0x0d, 0x01, 0x0a, 0x01, 0x05, 0x09, 0x01, 0x0f, 0x06, 0x0e,
            0x04, 0x04, 0x0b, 0x04, 0x0b, 0x0f
        ];
        let solved_grid: [usize; 0x10] = [1,2,3,4,5,6,7,8,9,0xa,0xb,0xc,0xd,0xe,0xf,0];

        let mut fixed_moves: HashMap<usize, usize> = HashMap::new();

        for i in vec![4, 0xd, 0x16, 0x1f, 0x28, 0x31] {
            fixed_moves.insert(i, all_moves[i]);
        }

        let mut move_limit: [isize; 0x10] = [0; 0x10];

        for mv in all_moves.iter() {
            move_limit[*mv] += 1;
        }

        Board {
            board: board,
            moves: Vec::new(),
            max_moves: 0x36,
            move_number: 0,
            empt_idx: empt_idx,
            solved_grid: solved_grid,
            fixed_moves: fixed_moves,
            move_limit: move_limit,
        }
    }

    pub fn solved(&self) -> bool {
        self.board == self.solved_grid
    }

    pub fn get_move(&self, off: Vec<isize>) -> Option<usize> {
        let empt_idx: isize = self.empt_idx.try_into().unwrap();
        let empt_i: isize = empt_idx / 4;
        let empt_j: isize = empt_idx % 4;
        let src_i: isize = empt_i + off[0];
        let src_j: isize = empt_j + off[1];
        if src_i < 4 && src_i >= 0 && src_j < 4 && src_j >= 0 {
            let idx: usize = (src_i * 4 + src_j).try_into().unwrap();
            return Some(self.board[idx])
        }
        None
    }

    pub fn generate_moves(&self) -> Vec<usize> {
        let mut moves: Vec<usize> = Vec::new();

        for off in vec![vec![-1, 0], vec![1, 0], vec![0, -1], vec![0, 1]] {
            let maybe_move = self.get_move(off);
            if let Some(mv) = maybe_move {
                moves.push(mv);
            }
        }

        moves
    }

    pub fn apply_move(&mut self, mv: usize, undo: bool) {
        let i: usize = self.board.iter().position(|&x| x == mv).unwrap();
        let tmp: usize = self.board[i];
        self.board[i] = self.board[self.empt_idx];
        self.board[self.empt_idx] = tmp;
        self.empt_idx = i;
        if undo {
            self.move_number -= 1;
            self.moves.pop();
            self.move_limit[mv] += 1;
        }
        else {
            self.move_number += 1;
            self.moves.push(mv);
            self.move_limit[mv] -= 1;
        }
    }

    pub fn manhattan_distance(&self, mv: usize) -> isize {
        let mv_idx: isize = self.board.iter().position(|&x| x == mv).unwrap().try_into().unwrap();
        let mv_i: isize = mv_idx / 4;
        let mv_j: isize = mv_idx % 4;

        let supposed_idx: isize = (mv - 1).try_into().unwrap();
        let supposed_i: isize = supposed_idx / 4;
        let supposed_j: isize = supposed_idx % 4;

        let manhattan: isize = (supposed_j - mv_j).abs() + (supposed_i - mv_i).abs();

        manhattan
    }

    pub fn solve(&mut self) -> bool {

        // GG
        if self.solved() {
            return true;
        }
        
        // No more moves
        if self.move_number >= self.max_moves {
            return false;
        }

        // Last move need to be 0xc or 0xf
        if self.move_limit[0xc] <= 0 && self.move_limit[0xf] <= 0 {
            return false;
        }

        let last_move: Option<usize> = self.moves.last().copied();

        if let Some(mv) = last_move {
            // Tile cannot possibly go back to its supposed location
            let man: isize = self.manhattan_distance(mv);
            if self.move_limit[mv] < man {
                return false
            }
        }

        // Generate possible moves from current grid
        let mut moves: Vec<usize> = self.generate_moves();

        // Cannot apply same move twice
        if let Some(mv) = last_move {
            moves = moves.iter().filter(|&x| *x != mv).cloned().collect();
        }

        // Filter fixed moves from the cube center tiles
        if self.fixed_moves.contains_key(&self.move_number) {
            let mv: usize = *self.fixed_moves.get(&self.move_number).unwrap();
            moves = moves.iter().filter(|&x| *x == mv).cloned().collect();
        }


        for mv in moves {
            // Apply move
            self.apply_move(mv, false);
            // Recursive call
            let solved: bool = self.solve();
            // GG
            if solved {
                return true;
            }
            // Undo move
            self.apply_move(mv, true);
        }

        false
    }
}


fn solve() {
    let arr: [usize; 0x10] = [
        3, 0xd, 0xa, 8,
        0xe, 0, 9, 1,
        5, 0xf, 2, 0xc,
        4, 0xb, 6, 7
    ];

    let mut board: Board = Board::new(arr);

    board.solve();

    println!("{:x?}", board.moves);
}

fn main() {
    solve()
}
