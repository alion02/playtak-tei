use std::fs::File;
use std::io::{self, BufRead, BufReader};
use std::path::Path;

use rand::prelude::IndexedRandom;
use rand::rng;

use crate::game::{Direction, GameMove};

pub struct Book {
    lines: Vec<Vec<GameMove>>,
}

impl Book {
    pub fn load(path: impl AsRef<Path>) -> io::Result<Self> {
        let file = File::open(path)?;
        let reader = BufReader::new(file);
        let mut lines = Vec::new();

        for line in reader.lines() {
            let line = line?;
            if line.trim().is_empty() {
                continue;
            }
            let mut moves = Vec::new();
            for move_str in line.split_ascii_whitespace() {
                if let Ok(m) = GameMove::from_ptn(move_str) {
                    moves.push(m);
                } else {
                    // Stop parsing this line if an invalid move is encountered
                    break;
                }
            }
            if !moves.is_empty() {
                lines.push(moves);
            }
        }

        Ok(Self { lines })
    }

    pub fn get_move(&self, history: &[GameMove], size: u32) -> Option<GameMove> {
        let matching_next_moves: Vec<&GameMove> = self.lines.iter()
            .filter_map(|line| {
                if line.len() > history.len() && line.starts_with(history) {
                    let next_move = &line[history.len()];
                    if self.is_valid(next_move, size) {
                        Some(next_move)
                    } else {
                        None
                    }
                } else {
                    None
                }
            })
            .collect();

        if matching_next_moves.is_empty() {
            None
        } else {
            let mut rng = rng();
            matching_next_moves.choose(&mut rng).map(|&m| m.clone())
        }
    }

    fn is_valid(&self, m: &GameMove, size: u32) -> bool {
        match m {
            GameMove::Place { x, y, .. } => *x < size && *y < size,
            GameMove::Spread {
                x,
                y,
                direction,
                drops,
            } => {
                if *x >= size || *y >= size {
                    return false;
                }
                let distance = drops.len() as u32;
                match direction {
                    Direction::North => *y + distance < size,
                    Direction::South => *y >= distance,
                    Direction::East => *x + distance < size,
                    Direction::West => *x >= distance,
                }
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_book_loading_and_selection() {
        // Create a dummy book file
        let book_content = "a1 b1\na1 c1\n";
        let path = "test.book";
        std::fs::write(path, book_content).unwrap();

        let book = Book::load(path).unwrap();
        std::fs::remove_file(path).unwrap();

        assert_eq!(book.lines.len(), 2);

        // Test selection
        let history = vec![GameMove::from_ptn("a1").unwrap()];
        let next_move = book.get_move(&history, 5).unwrap();
        
        // Should be b1 or c1
        let b1 = GameMove::from_ptn("b1").unwrap();
        let c1 = GameMove::from_ptn("c1").unwrap();
        
        assert!(next_move == b1 || next_move == c1);
    }
    
    #[test]
    fn test_invalid_moves_filtered() {
        let book_content = "a1 f6\n"; // f6 is invalid on 5x5
        let path = "test_invalid.book";
        std::fs::write(path, book_content).unwrap();
        
        let book = Book::load(path).unwrap();
        std::fs::remove_file(path).unwrap();
        
        let history = vec![GameMove::from_ptn("a1").unwrap()];
        let next_move = book.get_move(&history, 5); // Size 5
        
        assert!(next_move.is_none());
        
        let next_move_6 = book.get_move(&history, 6); // Size 6
        assert!(next_move_6.is_some());
    }
}
